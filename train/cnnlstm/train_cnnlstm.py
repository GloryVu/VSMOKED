from CNNLSTM.model import CNNLSTM
from STCNet.src.STCNet_mobilenetv2.stcnet import STCNet
from dataset.dataset import SmokeDataset
import torch
from tqdm import tqdm
from torch import nn
from torch.utils.data import DataLoader
from torchvision import transforms
from time import sleep
import warnings
import numpy as np
from torch.utils.data.sampler import SubsetRandomSampler
warnings.filterwarnings("ignore")

device = ("cuda" if torch.cuda.is_available() else "cpu")
model = STCNet()
random_transform=model.get_augmentation()
hard_transform=transforms.Compose(
        [transforms.ToTensor(), transforms.Normalize((0.5, 0.5, 0.5), (0.5, 0.5, 0.5))])
train_set = SmokeDataset(r"dataset/wildfire_smoke_dataset/classification/train",random_transform,hard_transform,15)
test_set = SmokeDataset(r"dataset/wildfire_smoke_dataset/classification/test",None,hard_transform,15)
batch_size = 64

train_loader = DataLoader(dataset=train_set, batch_size=64, pin_memory=True, shuffle=True)
valid_loader = DataLoader(dataset=test_set, batch_size=64, pin_memory=True, shuffle=True)

model = CNNLSTM().to(device)

criterion = nn.CrossEntropyLoss()
optimizer = torch.optim.Adam(model.parameters(), lr=0.0003)

model.train()

num_epochs = 30

best_val_acc = 0

for epoch in range(num_epochs):
    # if epoch % 1 == 0:
    loop = tqdm(train_loader, total=len(train_loader) + len(valid_loader), position=0, leave=False)
    # else:
    #     loop = tqdm(train_loader, total=len(train_loader), position=0, leave=False)

    for x, y in train_loader:
        loop.set_description(f"Epoch [{epoch + 1}/{num_epochs}], Training")

        x = x.to(device=device)
        y = y.to(device=device)

        outputs = model(x)

        loss = criterion(outputs, y)
        optimizer.zero_grad()
        loss.backward()
        optimizer.step()

        loop.set_postfix(train_loss=loss.item())
        loop.update(1)

    if epoch % 1 == 0:
        num_correct = 0
        num_samples = 0
        model.eval()

        with torch.no_grad():
            for x, y in valid_loader:
                loop.set_description(f"Epoch [{epoch + 1}/{num_epochs}], Validing")
                x = x.to(device=device)
                y = y.to(device=device)

                pred = model(x)
                pred_idx = torch.argmax(pred, dim=1)

                num_correct += (pred_idx == y).sum().item()
                num_samples += y.size(0)

                val_acc = round(num_correct / num_samples, 3)

                if val_acc > best_val_acc:
                    best_val_acc = val_acc
                    torch.save(model.state_dict(), "CNNLSTM/save/model_best.pth")

                loop.set_postfix(val_accuracy=val_acc)
                loop.update(1)
                sleep(1)

        model.train()