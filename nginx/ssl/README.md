# TLS Certificates

Nginx expects the following files in this directory at runtime:

- `cert.pem` — full certificate chain (server cert + any intermediates)
- `key.pem`  — private key (mode `600`, owned by the nginx user)

This directory is mounted read-only into the nginx container at
`/etc/nginx/ssl` (see `docker-compose.prod.yml`).

## Obtaining certificates (Let's Encrypt)

1. Point DNS for your production domain at the server.
2. From the project root, run certbot in webroot mode against the
   `nginx/certbot` directory, e.g.:

   ```bash
   docker run --rm \
     -v $(pwd)/nginx/certbot:/var/www/certbot \
     -v $(pwd)/nginx/letsencrypt:/etc/letsencrypt \
     certbot/certbot certonly --webroot \
       -w /var/www/certbot \
       -d your.domain.com \
       --email ops@your.domain.com --agree-tos --no-eff-email
   ```

3. Copy the issued `fullchain.pem` → `cert.pem` and `privkey.pem` → `key.pem`
   into this directory, then reload nginx:

   ```bash
   docker compose -f docker-compose.prod.yml exec nginx nginx -s reload
   ```

## Renewal

Let's Encrypt certificates expire every 90 days. Schedule a cron job on the
host that re-runs the certbot command above and reloads nginx. The nginx
server already serves `/.well-known/acme-challenge/` over plain HTTP so
renewals work without downtime.

## Local development

For local dev you can generate a self-signed cert:

```bash
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout key.pem -out cert.pem \
  -subj "/CN=localhost"
```

Do NOT commit real certificates or keys to the repository.
