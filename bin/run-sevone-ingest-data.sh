podman run --rm \
  -v /var/custom/ps-addons/APPNAMEREPLACE/etc:/app/etc:ro \
  -v /var/custom/ps-addons/APPNAMEREPLACE/input:/app/input:ro \
  -v /var/custom/ps-addons/APPNAMEREPLACE/archive:/app/archive:rw \
  APPNAMEREPLACE