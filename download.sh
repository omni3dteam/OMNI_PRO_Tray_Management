sudo systemctl stop tray_management.service
wget https://github.com/omni3dteam/OMNI_PRO_Tray_Management/releases/download/%2Bv0.1/tray_management.tar.gz
tar -xf tray_management.tar.gz
sudo systemctl start tray_management.service