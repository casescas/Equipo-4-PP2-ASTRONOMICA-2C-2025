#Preparacion del Entorno
import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader
from torchvision import transforms, models
from PIL import Image
from sklearn.utils.class_weight import compute_class_weight
from sklearn.model_selection import train_test_split
from sklearn.metrics import confusion_matrix, ConfusionMatrixDisplay, precision_recall_fscore_support, accuracy_score

#Verificar uso e intalacion de GPU
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print(f"Dispositivo usado: {device}")

#Ruta del dataset donde esta almacenado las imagenes.
base_dir = r'Ruta donde estar el Datasets [04.Imagenes_validacion_manual]'

#Cargar imágenes y etiquetas
image_paths, octa_labels = [], []
for folder in os.listdir(base_dir):
    folder_path = os.path.join(base_dir, folder)
    if not os.path.isdir(folder_path):
        continue
    try:
        octa = int(folder.split('_')[-1])
    except ValueError:
        continue
    for fname in os.listdir(folder_path):
        if fname.lower().endswith(('.jpg', '.jpeg', '.png')):
            image_paths.append(os.path.join(folder_path, fname))
            octa_labels.append(octa)

#Visualización del balanceo de clases
plt.figure(figsize=(8, 4))
sns.countplot(x=octa_labels)
plt.title("Distribución de clases (Octas)")
plt.xlabel("Nivel de Octa")
plt.ylabel("Cantidad de imágenes")
plt.savefig("distribucion_clases_octas.png")
plt.close()

#División del Dataset en Entrenamiento y Validación  (80/20)
train_paths, val_paths, train_labels, val_labels = train_test_split(
    image_paths, octa_labels, test_size=0.2, random_state=42, stratify=octa_labels)

#Pesos de clase
class_weights = compute_class_weight(class_weight='balanced', classes=np.unique(octa_labels), y=octa_labels)
class_weights_tensor = torch.tensor(class_weights, dtype=torch.float).to(device)

#Clases minoritarias
counts = pd.Series(octa_labels).value_counts()
minority_classes = counts[counts < counts.mean()].index.tolist()
print("Clases minoritarias detectadas:", minority_classes)

#Dataset personalizado
class OctaDataset(Dataset):
    def __init__(self, image_paths, labels, img_width, img_height, augment=False, minority_classes=None, oversample_factor=2):
        self.img_width = img_width
        self.img_height = img_height
        self.augment = augment
        self.minority_classes = minority_classes if minority_classes else []
        self.image_paths = image_paths.copy()
        self.labels = labels.copy()

        #Oversampling dinámico
        if self.minority_classes:
            for i, lbl in enumerate(labels):
                if lbl in self.minority_classes:
                    for _ in range(oversample_factor - 1):
                        self.image_paths.append(image_paths[i])
                        self.labels.append(lbl)

        #Transformaciones
        normalize = transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
        if self.augment:
            self.transform = transforms.Compose([
                transforms.Resize((img_height, img_width)),
                transforms.RandomHorizontalFlip(),
                transforms.RandomRotation(40),
                transforms.ColorJitter(brightness=0.6, contrast=0.6),
                transforms.RandomAffine(degrees=0, translate=(0.15, 0.15), shear=25),
                transforms.RandomResizedCrop((img_height, img_width), scale=(0.7, 1.0)),
                transforms.GaussianBlur(kernel_size=3),
                transforms.ToTensor(),
                normalize
            ])
        else:
            self.transform = transforms.Compose([
                transforms.Resize((img_height, img_width)),
                transforms.ToTensor(),
                normalize
            ])
            
    #Métodos __len__ y __getitem__
    def __len__(self):
        return len(self.image_paths)

    def __getitem__(self, idx):
        img_path = self.image_paths[idx]
        label = self.labels[idx]
        try:
            image = Image.open(img_path).convert('RGB')
            image = self.transform(image)
        except Exception as e:
            print(f"Error al cargar imagen: {img_path} — {e}")
            image = torch.zeros(3, self.img_height, self.img_width)
        return image, label

#Configuración de Parámetros y Creación de DataLoaders
img_width, img_height = 224, 224
batch_size = 64

train_dataset = OctaDataset(train_paths, train_labels, img_width, img_height, augment=True, 
                minority_classes=minority_classes, oversample_factor=3)
val_dataset = OctaDataset(val_paths, val_labels, img_width, img_height, augment=False)

train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
val_loader = DataLoader(val_dataset, batch_size=batch_size, shuffle=False)

#Definición del Modelo con Fine-Tuning Completo
model = models.efficientnet_b3(pretrained=True)
for param in model.parameters():
    param.requires_grad = True

#Ajustar clasificador
model.classifier[1] = nn.Linear(model.classifier[1].in_features, 9)
model = model.to(device)

#Función de Pérdida, Optimizador y Scheduler
class FocalLoss(nn.Module):  
    def __init__(self, alpha=1, gamma=2, reduction='mean'):
        super(FocalLoss, self).__init__()
        self.alpha = alpha
        self.gamma = gamma
        self.reduction = reduction

    def forward(self, inputs, targets):
        ce_loss = nn.CrossEntropyLoss(weight=class_weights_tensor)(inputs, targets)
        pt = torch.exp(-ce_loss)
        focal_loss = self.alpha * (1 - pt) ** self.gamma * ce_loss
        return focal_loss

criterion = FocalLoss()
optimizer = optim.Adam(model.parameters(), lr=1e-4, weight_decay=1e-4)
scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(optimizer, mode='min', factor=0.5, patience=5)

#Entrenamiento con Early Stopping
num_epochs = 100
patience = 8
best_val_loss = float('inf')
best_model_wts = model.state_dict()
epochs_no_improve = 0
train_loss_history, val_loss_history = [], []
train_acc_history, val_acc_history = [], []

for epoch in range(num_epochs):
    model.train()
    running_loss, correct, total = 0.0, 0, 0

    for images, labels in train_loader:
        images, labels = images.to(device), labels.to(device)
        optimizer.zero_grad()
        outputs = model(images)
        loss = criterion(outputs, labels)
        loss.backward()
        optimizer.step()

        running_loss += loss.item() * images.size(0)
        _, predicted = torch.max(outputs, 1)
        correct += (predicted == labels).sum().item()
        total += labels.size(0)

    train_loss = running_loss / total
    train_acc = correct / total
    train_loss_history.append(train_loss)
    train_acc_history.append(train_acc)

    #Validación
    model.eval()
    val_loss, correct, total = 0.0, 0, 0
    with torch.no_grad():
        for images, labels in val_loader:
            images, labels = images.to(device), labels.to(device)
            outputs = model(images)
            loss = criterion(outputs, labels)
            val_loss += loss.item() * images.size(0)
            _, predicted = torch.max(outputs, 1)
            correct += (predicted == labels).sum().item()
            total += labels.size(0)

    val_loss /= total
    val_acc = correct / total
    val_loss_history.append(val_loss)
    val_acc_history.append(val_acc)

    scheduler.step(val_loss)

    print(f"Época {epoch+1}/{num_epochs} — Loss: {train_loss:.4f} — Val Loss: {val_loss:.4f} — Acc: {train_acc:.4f} — Val Acc: {val_acc:.4f}")

    if val_loss < best_val_loss:
        best_val_loss = val_loss
        best_model_wts = model.state_dict()
        torch.save(model.state_dict(), "mejor_modelo_efficientnet_finetuning.pth")
        print("Mejor modelo guardado.")
        epochs_no_improve = 0
    else:
        epochs_no_improve += 1

    if epochs_no_improve >= patience:
        print("Early stopping activado.")
        break

model.load_state_dict(best_model_wts)

#Guardar historial
df_hist = pd.DataFrame({
    "loss": train_loss_history,
    "val_loss": val_loss_history,
    "accuracy": train_acc_history,
    "val_accuracy": val_acc_history
})
df_hist.to_csv("historial_entrenamiento.csv", index=False)

#Predicciones y métricas
model.eval()
y_pred_octa, octa_true = [], []
with torch.no_grad():
    for images, labels in val_loader:
        images = images.to(device)
        outputs = model(images)
        _, preds = torch.max(outputs, 1)
        y_pred_octa.extend(preds.cpu().numpy())
        octa_true.extend(labels.numpy())

cm = confusion_matrix(octa_true, y_pred_octa)
ConfusionMatrixDisplay(cm, display_labels=[str(i) for i in range(9)]).plot(cmap='Blues')
plt.title("Matriz de Confusión - Clasificación de Octas")
plt.savefig("matriz_confusion_octas.png")
plt.close()

precision, recall, f1, _ = precision_recall_fscore_support(octa_true, y_pred_octa, labels=list(range(9)), zero_division=0)
accuracy = accuracy_score(octa_true, y_pred_octa)

df_metrics = pd.DataFrame({
    "Clase": list(range(9)),
    "Precision": precision,
    "Recall": recall,
    "F1-score": f1
})
df_metrics.loc[len(df_metrics.index)] = ["Accuracy Global", accuracy, "", ""]
df_metrics.to_csv("metricas_modelo_octas.csv", index=False)

#Visualización de errores
errores = [(path, true, pred) for path, true, pred in zip(val_paths, octa_true, y_pred_octa) if true != pred]
plt.figure(figsize=(12, 12))
for i, (path, true, pred) in enumerate(errores[:9]):
    img = Image.open(path).resize((img_width, img_height))
    plt.subplot(3, 3, i + 1)
    plt.imshow(img)
    plt.title(f"Real: {true} - Pred: {pred}")
    plt.axis('off')
plt.tight_layout()
plt.savefig("errores_clasificacion_octas.png")
plt.close()

df_errores = pd.DataFrame(errores, columns=["Ruta", "Etiqueta Real", "Predicción"])
df_errores["Carpeta"] = df_errores["Ruta"].apply(lambda x: os.path.basename(os.path.dirname(x)))
df_errores.to_csv("errores_clasificacion.csv", index=False)
print("Archivo 'errores_clasificacion.csv' guardado con éxito.")

#Gráfico de aprendizaje
epochs_range = range(1, len(train_loss_history) + 1)
plt.figure(figsize=(10, 4))
plt.subplot(1, 2, 1)
plt.plot(epochs_range, train_loss_history, label='Train Loss')
plt.plot(epochs_range, val_loss_history, label='Validation Loss')
plt.title('Loss por época')
plt.xlabel('Épocas')
plt.ylabel('Loss')
plt.legend()

plt.subplot(1, 2, 2)
plt.plot(epochs_range, train_acc_history, label='Train Accuracy')
plt.plot(epochs_range, val_acc_history, label='Validation Accuracy')
plt.title('Accuracy por época')
plt.xlabel('Épocas')
plt.ylabel('Accuracy')
plt.legend()

plt.tight_layout()
plt.savefig("grafico_aprendizaje_octas.png")
plt.close()