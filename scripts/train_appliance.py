"""
Appliance Classification Training Pipeline

Trains a CNN model to classify appliance types and ON/OFF status.
"""

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Tuple, Any, Optional

import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader
from torchvision import transforms, models
from PIL import Image
from sklearn.model_selection import train_test_split


class ApplianceDataset(Dataset):
    """Dataset for appliance classification."""
    
    def __init__(
        self,
        data_dir: str,
        transform: Optional[transforms.Compose] = None,
        mode: str = 'type'  # 'type' for appliance type, 'status' for ON/OFF
    ):
        """
        Initialize dataset.
        
        Args:
            data_dir: Directory containing class subdirectories
            transform: Optional transforms to apply
            mode: Classification mode ('type' or 'status')
        """
        self.data_dir = Path(data_dir)
        self.transform = transform
        self.mode = mode
        self.samples = []
        
        # Load all image paths and labels
        self._load_dataset()
        
        # Create label mappings
        self._create_mappings()
    
    def _load_dataset(self):
        """Load all image paths and labels from directory structure."""
        for class_dir in self.data_dir.iterdir():
            if not class_dir.is_dir():
                continue
            
            class_name = class_dir.name
            parts = class_name.split('_')
            
            if len(parts) < 2:
                continue
            
            appliance_type = parts[0]
            status = parts[1]
            
            for img_path in class_dir.glob('*.jpg'):
                self.samples.append({
                    'path': str(img_path),
                    'type': appliance_type,
                    'status': status,
                    'class_name': class_name
                })
    
    def _create_mappings(self):
        """Create label to index mappings."""
        if self.mode == 'type':
            self.classes = sorted(set(s['type'] for s in self.samples))
        else:
            self.classes = sorted(set(s['status'] for s in self.samples))
        
        self.class_to_idx = {c: i for i, c in enumerate(self.classes)}
        self.idx_to_class = {i: c for c, i in self.class_to_idx.items()}
    
    def __len__(self) -> int:
        return len(self.samples)
    
    def __getitem__(self, idx: int) -> Tuple[torch.Tensor, int]:
        """Get a sample."""
        sample = self.samples[idx]
        
        # Load image
        image = Image.open(sample['path']).convert('RGB')
        
        if self.transform:
            image = self.transform(image)
        
        # Get label
        if self.mode == 'type':
            label = self.class_to_idx[sample['type']]
        else:
            label = self.class_to_idx[sample['status']]
        
        return image, label
    
    def get_class_weights(self) -> torch.Tensor:
        """Calculate class weights for imbalanced datasets."""
        counts = np.zeros(len(self.classes))
        for sample in self.samples:
            if self.mode == 'type':
                idx = self.class_to_idx[sample['type']]
            else:
                idx = self.class_to_idx[sample['status']]
            counts[idx] += 1
        
        weights = 1.0 / counts
        weights = weights / weights.sum() * len(self.classes)
        return torch.FloatTensor(weights)


class ApplianceClassifier(nn.Module):
    """CNN model for appliance classification."""
    
    def __init__(
        self,
        num_types: int,
        num_status: int,
        pretrained: bool = True,
        dropout: float = 0.5
    ):
        """
        Initialize model.
        
        Args:
            num_types: Number of appliance types
            num_status: Number of status classes (ON/OFF)
            pretrained: Use pretrained weights
            dropout: Dropout rate
        """
        super().__init__()
        
        # Use MobileNetV2 for efficiency
        self.backbone = models.mobilenet_v2(pretrained=pretrained)
        
        # Get feature dimension
        num_features = self.backbone.classifier[1].in_features
        
        # Remove original classifier
        self.backbone.classifier = nn.Identity()
        
        # Custom classifiers
        self.type_classifier = nn.Sequential(
            nn.Dropout(dropout),
            nn.Linear(num_features, 256),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(256, num_types)
        )
        
        self.status_classifier = nn.Sequential(
            nn.Dropout(dropout),
            nn.Linear(num_features, 256),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(256, num_status)
        )
        
        self.num_types = num_types
        self.num_status = num_status
    
    def forward(
        self,
        x: torch.Tensor,
        return_features: bool = False
    ) -> Dict[str, torch.Tensor]:
        """
        Forward pass.
        
        Args:
            x: Input tensor
            return_features: Return intermediate features
            
        Returns:
            Dictionary with type_logits and status_logits
        """
        features = self.backbone(x)
        
        type_logits = self.type_classifier(features)
        status_logits = self.status_classifier(features)
        
        if return_features:
            return {
                'type_logits': type_logits,
                'status_logits': status_logits,
                'features': features
            }
        
        return {
            'type_logits': type_logits,
            'status_logits': status_logits
        }


def get_transforms(train: bool = True, image_size: int = 224) -> transforms.Compose:
    """Get data transforms."""
    if train:
        return transforms.Compose([
            transforms.Resize((image_size, image_size)),
            transforms.RandomHorizontalFlip(),
            transforms.RandomRotation(15),
            transforms.ColorJitter(brightness=0.2, contrast=0.2),
            transforms.ToTensor(),
            transforms.Normalize(
                mean=[0.485, 0.456, 0.406],
                std=[0.229, 0.224, 0.225]
            )
        ])
    else:
        return transforms.Compose([
            transforms.Resize((image_size, image_size)),
            transforms.ToTensor(),
            transforms.Normalize(
                mean=[0.485, 0.456, 0.406],
                std=[0.229, 0.224, 0.225]
            )
        ])


def train_epoch(
    model: nn.Module,
    loader: DataLoader,
    criterion: nn.Module,
    optimizer: optim.Optimizer,
    device: torch.device,
    alpha: float = 0.5
) -> Dict[str, float]:
    """Train for one epoch."""
    model.train()
    
    running_type_loss = 0.0
    running_status_loss = 0.0
    running_type_correct = 0
    running_status_correct = 0
    running_total = 0
    
    for images, type_labels in loader:
        images = images.to(device)
        type_labels = type_labels.to(device)
        
        # For now, derive status from class name
        # In production, you'd have separate labels
        status_labels = (type_labels % 2).to(device)  # Simple hack for demo
        
        optimizer.zero_grad()
        
        outputs = model(images)
        
        type_loss = criterion(outputs['type_logits'], type_labels)
        status_loss = criterion(outputs['status_logits'], status_labels)
        
        loss = alpha * type_loss + (1 - alpha) * status_loss
        
        loss.backward()
        optimizer.step()
        
        running_type_loss += type_loss.item() * images.size(0)
        running_status_loss += status_loss.item() * images.size(0)
        
        _, type_preds = outputs['type_logits'].max(1)
        _, status_preds = outputs['status_logits'].max(1)
        
        running_type_correct += type_preds.eq(type_labels).sum().item()
        running_status_correct += status_preds.eq(status_labels).sum().item()
        
        running_total += images.size(0)
    
    return {
        'type_loss': running_type_loss / running_total,
        'status_loss': running_status_loss / running_total,
        'type_acc': running_type_correct / running_total,
        'status_acc': running_status_correct / running_total
    }


def evaluate(
    model: nn.Module,
    loader: DataLoader,
    criterion: nn.Module,
    device: torch.device
) -> Dict[str, float]:
    """Evaluate model."""
    model.eval()
    
    running_type_loss = 0.0
    running_status_loss = 0.0
    running_type_correct = 0
    running_status_correct = 0
    running_total = 0
    
    with torch.no_grad():
        for images, type_labels in loader:
            images = images.to(device)
            type_labels = type_labels.to(device)
            status_labels = (type_labels % 2).to(device)
            
            outputs = model(images)
            
            type_loss = criterion(outputs['type_logits'], type_labels)
            status_loss = criterion(outputs['status_logits'], status_labels)
            
            running_type_loss += type_loss.item() * images.size(0)
            running_status_loss += status_loss.item() * images.size(0)
            
            _, type_preds = outputs['type_logits'].max(1)
            _, status_preds = outputs['status_logits'].max(1)
            
            running_type_correct += type_preds.eq(type_labels).sum().item()
            running_status_correct += status_preds.eq(status_labels).sum().item()
            
            running_total += images.size(0)
    
    return {
        'type_loss': running_type_loss / running_total,
        'status_loss': running_status_loss / running_total,
        'type_acc': running_type_correct / running_total,
        'status_acc': running_status_correct / running_total
    }


def train_model(
    data_dir: str,
    epochs: int = 20,
    batch_size: int = 32,
    learning_rate: float = 0.001,
    image_size: int = 224,
    output_dir: str = 'models',
    device: Optional[str] = None
) -> str:
    """
    Train the appliance classifier.
    
    Args:
        data_dir: Directory containing training data
        epochs: Number of training epochs
        batch_size: Batch size
        learning_rate: Learning rate
        image_size: Input image size
        output_dir: Directory to save model
        device: Device to use ('cpu', 'cuda', or None for auto)
        
    Returns:
        Path to saved model
    """
    # Set device
    if device is None:
        device = 'cuda' if torch.cuda.is_available() else 'cpu'
    device = torch.device(device)
    
    print(f"Using device: {device}")
    
    # Load dataset
    train_transform = get_transforms(train=True, image_size=image_size)
    test_transform = get_transforms(train=False, image_size=image_size)
    
    # For training, use combined dataset
    full_dataset = ApplianceDataset(data_dir, train_transform, mode='type')
    
    # Split into train/val
    train_size = int(0.8 * len(full_dataset))
    val_size = len(full_dataset) - train_size
    
    # Simple random split
    indices = list(range(len(full_dataset)))
    np.random.shuffle(indices)
    train_indices = indices[:train_size]
    val_indices = indices[train_size:]
    
    # Create subsets
    class SubsetDataset(Dataset):
        def __init__(self, dataset, indices):
            self.dataset = dataset
            self.indices = indices
        
        def __len__(self):
            return len(self.indices)
        
        def __getitem__(self, idx):
            return self.dataset[self.indices[idx]]
    
    train_dataset = SubsetDataset(full_dataset, train_indices)
    val_dataset = SubsetDataset(full_dataset, val_indices)
    
    # Apply test transforms
    train_dataset.dataset.transform = test_transform
    val_dataset.dataset.transform = test_transform
    
    train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
    val_loader = DataLoader(val_dataset, batch_size=batch_size, shuffle=False)
    
    print(f"Training samples: {len(train_dataset)}")
    print(f"Validation samples: {len(val_dataset)}")
    print(f"Classes: {full_dataset.classes}")
    
    # Create model
    num_types = len(full_dataset.classes)
    num_status = 2  # ON/OFF
    
    model = ApplianceClassifier(num_types, num_status, pretrained=True)
    model = model.to(device)
    
    # Loss and optimizer
    criterion = nn.CrossEntropyLoss()
    optimizer = optim.Adam(model.parameters(), lr=learning_rate)
    scheduler = optim.lr_scheduler.StepLR(optimizer, step_size=10, gamma=0.1)
    
    # Training loop
    best_val_acc = 0.0
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    for epoch in range(epochs):
        train_metrics = train_epoch(model, train_loader, criterion, optimizer, device)
        val_metrics = evaluate(model, val_loader, criterion, device)
        
        scheduler.step()
        
        print(f"Epoch {epoch+1}/{epochs}")
        print(f"  Train - Type Loss: {train_metrics['type_loss']:.4f}, "
              f"Type Acc: {train_metrics['type_acc']:.4f}, "
              f"Status Acc: {train_metrics['status_acc']:.4f}")
        print(f"  Val   - Type Loss: {val_metrics['type_loss']:.4f}, "
              f"Type Acc: {val_metrics['type_acc']:.4f}, "
              f"Status Acc: {val_metrics['status_acc']:.4f}")
        
        # Save best model
        if val_metrics['type_acc'] > best_val_acc:
            best_val_acc = val_metrics['type_acc']
            model_path = output_path / 'appliance_classifier.pt'
            torch.save({
                'model_state_dict': model.state_dict(),
                'type_classes': full_dataset.classes,
                'num_types': num_types,
                'num_status': num_status,
                'image_size': image_size
            }, model_path)
            print(f"  Saved best model to {model_path}")
    
    # Save class mappings
    mappings = {
        'type_classes': full_dataset.classes,
        'type_to_idx': full_dataset.class_to_idx,
        'idx_to_type': full_dataset.idx_to_class,
        'num_types': num_types,
        'num_status': num_status
    }
    
    with open(output_path / 'class_mappings.json', 'w') as f:
        json.dump(mappings, f, indent=2)
    
    print(f"\nTraining complete! Best val accuracy: {best_val_acc:.4f}")
    return str(model_path)


def predict_image(
    model_path: str,
    image_path: str,
    device: Optional[str] = None
) -> Dict[str, Any]:
    """
    Predict appliance type and status for an image.
    
    Args:
        model_path: Path to trained model
        image_path: Path to input image
        device: Device to use
        
    Returns:
        Prediction dictionary
    """
    if device is None:
        device = 'cuda' if torch.cuda.is_available() else 'cpu'
    device = torch.device(device)
    
    # Load model
    checkpoint = torch.load(model_path, map_location=device)
    
    model = ApplianceClassifier(
        checkpoint['num_types'],
        checkpoint['num_status'],
        pretrained=False
    )
    model.load_state_dict(checkpoint['model_state_dict'])
    model = model.to(device)
    model.eval()
    
    # Load and preprocess image
    transform = get_transforms(train=False, image_size=224)
    image = Image.open(image_path).convert('RGB')
    image_tensor = transform(image).unsqueeze(0).to(device)
    
    # Predict
    with torch.no_grad():
        outputs = model(image_tensor)
        
        type_probs = torch.softmax(outputs['type_logits'], dim=1)
        status_probs = torch.softmax(outputs['status_logits'], dim=1)
        
        type_idx = type_probs.argmax().item()
        status_idx = status_probs.argmax().item()
        
        type_conf = type_probs[0, type_idx].item()
        status_conf = status_probs[0, status_idx].item()
    
    type_classes = checkpoint.get('type_classes', ['monitor', 'projector', 'light', 'ceiling_fan', 'wall_fan'])
    
    return {
        'appliance_type': type_classes[type_idx],
        'type_confidence': type_conf,
        'status': 'ON' if status_idx == 1 else 'OFF',
        'status_confidence': status_conf
    }


def main():
    parser = argparse.ArgumentParser(
        description='Train appliance classifier'
    )
    parser.add_argument(
        '--data-dir',
        default='data/appliances/raw',
        help='Directory containing training data'
    )
    parser.add_argument(
        '--epochs',
        type=int,
        default=20,
        help='Number of training epochs'
    )
    parser.add_argument(
        '--batch-size',
        type=int,
        default=32,
        help='Batch size'
    )
    parser.add_argument(
        '--lr',
        type=float,
        default=0.001,
        help='Learning rate'
    )
    parser.add_argument(
        '--output-dir',
        default='models',
        help='Output directory for model'
    )
    parser.add_argument(
        '--device',
        choices=['cpu', 'cuda'],
        help='Device to use'
    )
    parser.add_argument(
        '--predict',
        help='Predict on a single image'
    )
    parser.add_argument(
        '--model',
        default='models/appliance_classifier.pt',
        help='Model file for prediction'
    )
    
    args = parser.parse_args()
    
    if args.predict:
        # Run prediction
        result = predict_image(args.model, args.predict, args.device)
        print(f"Prediction: {result}")
    else:
        # Train model
        model_path = train_model(
            args.data_dir,
            args.epochs,
            args.batch_size,
            args.lr,
            output_dir=args.output_dir,
            device=args.device
        )
        print(f"Model saved to: {model_path}")


if __name__ == '__main__':
    sys.exit(main())
