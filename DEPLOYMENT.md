# Deployment Guide for Ubuntu VPS

## Ports to Open

You need to open **2 ports** in your firewall:

- **Port 3000** - React Frontend
- **Port 8010** - Flask Backend API

## Firewall Configuration (UFW)

```bash
# Allow ports 3000 and 8010
sudo ufw allow 3000/tcp
sudo ufw allow 8010/tcp

# Enable firewall (if not already enabled)
sudo ufw enable

# Check firewall status
sudo ufw status
```

## Firewall Configuration (iptables)

If you're using iptables instead of UFW:

```bash
# Allow ports 3000 and 8010
sudo iptables -A INPUT -p tcp --dport 3000 -j ACCEPT
sudo iptables -A INPUT -p tcp --dport 8010 -j ACCEPT

# Save rules (Ubuntu/Debian)
sudo iptables-save | sudo tee /etc/iptables/rules.v4
```

## Cloud Provider Firewall

If you're using a cloud provider (AWS, DigitalOcean, etc.), also configure their firewall/security groups:

- **AWS EC2**: Add inbound rules for ports 3000 and 8010 in Security Groups
- **DigitalOcean**: Configure Firewall rules in Networking section
- **Google Cloud**: Add firewall rules in VPC Network > Firewall

## Accessing the Application

After opening the ports:

1. **Frontend**: `http://YOUR_VPS_IP:3000`
2. **Backend API**: `http://YOUR_VPS_IP:8010/api`

## Security Considerations

### For Production:

1. **Use a Reverse Proxy (Recommended)**:
   - Set up Nginx or Apache to proxy requests
   - Use HTTPS with Let's Encrypt
   - Only expose ports 80 and 443

2. **Bind Flask to localhost in production**:
   ```bash
   export FLASK_HOST=127.0.0.1
   python app.py
   ```
   Then configure Nginx to proxy to `http://127.0.0.1:8010`

3. **Use environment variables for API URL**:
   ```bash
   # In frontend/.env
   VITE_API_BASE=http://YOUR_VPS_IP:8010/api
   ```

## Running with Screen/Tmux (Recommended for VPS)

Since you're on a VPS, use `screen` or `tmux` to keep processes running:

```bash
# Install screen
sudo apt install screen

# Start all processes in separate screen sessions
screen -S redis -d -m redis-server
screen -S flask -d -m bash -c "cd ~/Documents/scrapping && source venv/bin/activate && python app.py"
screen -S celery-worker -d -m bash -c "cd ~/Documents/scrapping && source venv/bin/activate && python -m celery -A celery_app worker --pool=prefork --concurrency=4 --loglevel=info"
screen -S celery-beat -d -m bash -c "cd ~/Documents/scrapping && source venv/bin/activate && python -m celery -A celery_app beat --loglevel=info"
screen -S frontend -d -m bash -c "cd ~/Documents/scrapping/frontend && npm run dev -- --host 0.0.0.0"

# View running sessions
screen -ls

# Attach to a session (e.g., to see logs)
screen -r flask

# Detach: Press Ctrl+A then D
```

## Frontend Host Binding

The frontend needs to bind to `0.0.0.0` to accept external connections:

```bash
cd frontend
npm run dev -- --host 0.0.0.0
```

Or update `vite.config.js`:
```javascript
server: {
  host: '0.0.0.0',
  port: 3000,
}
```

