import os
import cv2
import torch
import numpy as np
import soundfile as sf
from pathlib import Path
from torch.utils.data import Dataset, DataLoader


class LazyImageDataset(Dataset):
    """
    Loads images lazily — reads from disk only when needed.
    Saves RAM significantly.
    """
    def __init__(
        self,
        folder: str,
        patch_size: int = 128,
        patches_per_image: int = 8
    ):
        self.patch_size        = patch_size
        self.patches_per_image = patches_per_image
        self.image_paths       = []

        folder_path = Path(str(folder))
        for ext in ["*.jpg", "*.png", "*.jpeg", "*.bmp"]:
            self.image_paths.extend(
                list(folder_path.glob(ext))
            )

        self.total = len(self.image_paths) * patches_per_image
        print(f"LazyImageDataset: {len(self.image_paths)} images "
              f"→ {self.total} patches (lazy)")

    def __len__(self):
        return self.total

    def __getitem__(self, idx):
        # figure out which image and which patch
        img_idx   = idx // self.patches_per_image
        img_path  = self.image_paths[
            img_idx % len(self.image_paths)
        ]

        # load image from disk
        img = cv2.imread(str(img_path), cv2.IMREAD_GRAYSCALE)
        if img is None:
            return torch.rand(1, self.patch_size, self.patch_size)

        h, w = img.shape
        if h < self.patch_size or w < self.patch_size:
            img  = cv2.resize(
                img,
                (self.patch_size * 2, self.patch_size * 2)
            )
            h, w = img.shape

        # random patch
        top   = np.random.randint(0, h - self.patch_size)
        left  = np.random.randint(0, w - self.patch_size)
        patch = img[
            top:top+self.patch_size,
            left:left+self.patch_size
        ]

        return torch.tensor(
            patch, dtype=torch.float32
        ).unsqueeze(0) / 255.0


class LazyVideoDataset(Dataset):
    """
    Loads video frames lazily — reads from disk when needed.
    """
    def __init__(
        self,
        folder: str,
        patch_size: int = 128,
        patches_per_video: int = 16,
        max_frames: int = 30
    ):
        self.patch_size        = patch_size
        self.patches_per_video = patches_per_video
        self.max_frames        = max_frames
        self.video_paths       = []

        folder_path = Path(str(folder))
        for ext in ["*.mp4", "*.avi", "*.mov"]:
            self.video_paths.extend(
                list(folder_path.glob(ext))
            )

        self.total = len(self.video_paths) * patches_per_video
        print(f"LazyVideoDataset: {len(self.video_paths)} videos "
              f"→ {self.total} patches (lazy)")

    def __len__(self):
        return self.total

    def __getitem__(self, idx):
        video_idx  = idx // self.patches_per_video
        video_path = self.video_paths[
            video_idx % len(self.video_paths)
        ]

        cap   = cv2.VideoCapture(str(video_path))
        total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

        if total == 0:
            cap.release()
            return torch.rand(1, self.patch_size, self.patch_size)

        # seek to random frame
        frame_idx = np.random.randint(
            0, min(total, self.max_frames)
        )
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
        ret, frame = cap.read()
        cap.release()

        if not ret or frame is None:
            return torch.rand(1, self.patch_size, self.patch_size)

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        h, w = gray.shape

        if h < self.patch_size or w < self.patch_size:
            return torch.rand(1, self.patch_size, self.patch_size)

        top   = np.random.randint(0, h - self.patch_size)
        left  = np.random.randint(0, w - self.patch_size)
        patch = gray[
            top:top+self.patch_size,
            left:left+self.patch_size
        ]

        return torch.tensor(
            patch, dtype=torch.float32
        ).unsqueeze(0) / 255.0


class LazyAudioDataset(Dataset):
    """
    Loads audio lazily — reads from disk when needed.
    """
    def __init__(
        self,
        folder: str,
        patch_size: int = 128,
        patches_per_file: int = 4
    ):
        self.patch_size       = patch_size
        self.patches_per_file = patches_per_file
        self.audio_paths      = []

        folder_path = Path(str(folder))
        for ext in ["*.wav", "*.flac"]:
            self.audio_paths.extend(
                list(folder_path.glob(ext))
            )

        self.total = len(self.audio_paths) * patches_per_file
        print(f"LazyAudioDataset: {len(self.audio_paths)} files "
              f"→ {self.total} patches (lazy)")

    def __len__(self):
        return self.total

    def __getitem__(self, idx):
        file_idx   = idx // self.patches_per_file
        audio_path = self.audio_paths[
            file_idx % len(self.audio_paths)
        ]

        try:
            data, sr = sf.read(str(audio_path))
            if len(data.shape) > 1:
                data = data.mean(axis=1)
            data = data.astype(np.float32)

            n_fft  = 512
            hop    = 128
            frames = []

            for start in range(
                0, len(data) - n_fft, hop
            ):
                frame = data[start:start + n_fft]
                spec  = np.abs(np.fft.rfft(frame))
                frames.append(spec)

            if len(frames) < self.patch_size:
                return torch.rand(
                    1, self.patch_size, self.patch_size
                )

            spec_2d = np.array(frames).T
            if spec_2d.max() > 0:
                spec_2d = spec_2d / spec_2d.max()

            freq_bins, time_frames = spec_2d.shape
            if (freq_bins  < self.patch_size or
                    time_frames < self.patch_size):
                return torch.rand(
                    1, self.patch_size, self.patch_size
                )

            top   = np.random.randint(
                0, freq_bins  - self.patch_size
            )
            left  = np.random.randint(
                0, time_frames - self.patch_size
            )
            patch = spec_2d[
                top:top+self.patch_size,
                left:left+self.patch_size
            ].astype(np.float32)

            return torch.tensor(patch).unsqueeze(0)

        except Exception:
            return torch.rand(
                1, self.patch_size, self.patch_size
            )


def get_combined_loader(
    data_folder: str,
    batch_size: int  = 16,
    patch_size: int  = 128,
    num_workers: int = 2
):
    """
    Creates lazy DataLoader — minimal RAM usage.
    Reads from disk on demand.
    """
    from torch.utils.data import ConcatDataset

    datasets     = []
    image_folder = os.path.join(data_folder, "images")
    video_folder = os.path.join(data_folder, "videos")
    audio_folder = os.path.join(data_folder, "audio")

    if os.path.exists(image_folder):
        datasets.append(
            LazyImageDataset(image_folder, patch_size)
        )
    if os.path.exists(video_folder):
        datasets.append(
            LazyVideoDataset(video_folder, patch_size)
        )
    if os.path.exists(audio_folder):
        datasets.append(
            LazyAudioDataset(audio_folder, patch_size)
        )

    if not datasets:
        print("No training data found — using synthetic")
        return None

    combined = ConcatDataset(datasets)
    total    = len(combined)
    print(f"\nTotal training patches: {total} (lazy loading)")

    return DataLoader(
        combined,
        batch_size=batch_size,
        shuffle=True,
        drop_last=True,
        num_workers=num_workers,
        pin_memory=True,     # faster GPU transfer
        prefetch_factor=2    # prefetch 2 batches ahead
    )