import os
import cv2
import torch
import numpy as np
import soundfile as sf
from pathlib import Path
from torch.utils.data import Dataset, DataLoader

class VideoFrameDataset(Dataset):
    """Extract Y channel frames from videos"""
    
    def __init__(self, folder: str, frame_size=64, max_frames=1000):
        self.frames = []
        folder = Path(folder)
        
        for video_path in folder.glob("*.mp4"):
            frames = self._extract_frames(
                str(video_path), frame_size, max_frames
            )
            self.frames.extend(frames)
        
        for video_path in folder.glob("*.avi"):
            frames = self._extract_frames(
                str(video_path), frame_size, max_frames
            )
            self.frames.extend(frames)
            
        print(f"Loaded {len(self.frames)} frames from {folder}")

    def _extract_frames(self, path, size, max_frames):
        frames = []
        cap    = cv2.VideoCapture(path)
        count  = 0
        
        while count < max_frames:
            ret, frame = cap.read()
            if not ret:
                break
            # convert to grayscale Y channel
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            gray = cv2.resize(gray, (size, size))
            # normalize to 0-1
            tensor = torch.tensor(
                gray, dtype=torch.float32
            ).unsqueeze(0) / 255.0
            frames.append(tensor)
            count += 1
            
        cap.release()
        return frames

    def __len__(self):
        return len(self.frames)

    def __getitem__(self, idx):
        return self.frames[idx]


class ImageDataset(Dataset):
    """Load images as Y channel patches"""
    
    def __init__(self, folder: str, patch_size=64):
        self.patches = []
        folder       = Path(folder)
        extensions   = ["*.jpg", "*.png", "*.jpeg", "*.bmp"]

        for ext in extensions:
            for img_path in folder.glob(ext):
                patches = self._extract_patches(
                    str(img_path), patch_size
                )
                self.patches.extend(patches)

        print(f"Loaded {len(self.patches)} patches from {folder}")

    def _extract_patches(self, path, size):
        patches = []
        img     = cv2.imread(path, cv2.IMREAD_GRAYSCALE)
        if img is None:
            return patches

        img = cv2.resize(img, (256, 256))
        # extract non-overlapping patches
        for i in range(0, 256 - size, size):
            for j in range(0, 256 - size, size):
                patch = img[i:i+size, j:j+size]
                tensor = torch.tensor(
                    patch, dtype=torch.float32
                ).unsqueeze(0) / 255.0
                patches.append(tensor)

        return patches

    def __len__(self):
        return len(self.patches)

    def __getitem__(self, idx):
        return self.patches[idx]


class AudioDataset(Dataset):
    """Convert audio spectrograms to image patches"""

    def __init__(self, folder: str, patch_size=64):
        self.patches = []
        folder       = Path(folder)

        for wav_path in folder.glob("*.wav"):
            patches = self._extract_spectrogram_patches(
                str(wav_path), patch_size
            )
            self.patches.extend(patches)

        print(f"Loaded {len(self.patches)} audio patches from {folder}")

    def _extract_spectrogram_patches(self, path, size):
        patches = []
        try:
            data, sr = sf.read(path)
            # convert to mono
            if len(data.shape) > 1:
                data = data.mean(axis=1)

            # compute spectrogram
            spec = np.abs(np.fft.rfft(
                data.reshape(-1, 512), axis=1
            )).astype(np.float32)

            # normalize
            if spec.max() > 0:
                spec = spec / spec.max()

            # resize to 256x256 and extract patches
            spec_resized = cv2.resize(spec, (256, 256))

            for i in range(0, 256 - size, size):
                for j in range(0, 256 - size, size):
                    patch = spec_resized[i:i+size, j:j+size]
                    tensor = torch.tensor(
                        patch, dtype=torch.float32
                    ).unsqueeze(0)
                    patches.append(tensor)

        except Exception as e:
            print(f"Error loading {path}: {e}")

        return patches

    def __len__(self):
        return len(self.patches)

    def __getitem__(self, idx):
        return self.patches[idx]


def get_combined_loader(
    data_folder: str,
    batch_size: int = 4,
    patch_size: int = 64
) -> DataLoader:
    """
    Load all media types from a folder and combine into one DataLoader.
    Expects subfolders: videos/, images/, audio/
    """
    all_data = []

    video_folder = os.path.join(data_folder, "videos")
    image_folder = os.path.join(data_folder, "images")
    audio_folder = os.path.join(data_folder, "audio")

    if os.path.exists(video_folder):
        video_ds = VideoFrameDataset(video_folder, patch_size)
        all_data.extend(video_ds.frames)

    if os.path.exists(image_folder):
        image_ds = ImageDataset(image_folder, patch_size)
        all_data.extend(image_ds.patches)

    if os.path.exists(audio_folder):
        audio_ds = AudioDataset(audio_folder, patch_size)
        all_data.extend(audio_ds.patches)

    if not all_data:
        print("No training data found — using synthetic fallback")
        return None

    print(f"\nTotal training samples: {len(all_data)}")

    return DataLoader(
        all_data,
        batch_size=batch_size,
        shuffle=True,
        drop_last=True
    )