# noisypi
A little repo for a noisy box

## Boot
To get this thing to run on boot, we need to do the following:


### .venv

If you haven't made a venv already, we need to do that:

```bash
cd ~/noisypi
python -m venv .venv
./.venv/bin/python -m pip install -r requirements.txt
```

### systemctl config

Then make a service file in:  
`/etc/systemd/system/noisebox.service`

Add the following:

```bash
[Unit]
Description=NoiseBox

[Service]
Type=simple
WorkingDirectory=/home/pi/noisypi
ExecStart=/home/pi/noisypi/.venv/bin/python /home/pi/noisypi/noisebox.py
Restart=always                 # auto-restart on crash
RestartSec=3                   # little delay before respawn
PIDFile=/run/noisebox.pid
RuntimeDirectory=noisebox

[Install]
WantedBy=multi-user.target
```

Then run:
```bash
sudo systemctl daemon-reload
sudo systemctl enable noisebox.service
sudo systemctl start noisebox.service
```