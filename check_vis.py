import torch
print('CUDA available:', torch.cuda.is_available())
print('GPU:', torch.cuda.get_device_name(0))

# test a real training step timing
import time
from core.neural.trainer import GANTrainer

trainer = GANTrainer()
cover   = torch.rand(4, 1, 64, 64).cuda()
payload = torch.rand(4, 1, 64, 64).cuda()

# warmup
trainer.train_step(cover, payload)

# time 10 steps
start = time.time()
for _ in range(10):
    trainer.train_step(cover, payload)
torch.cuda.synchronize()
elapsed = (time.time() - start) / 10 * 1000
print(f'ms per step: {elapsed:.1f}ms')
print(f'Expected: 20-30ms')
