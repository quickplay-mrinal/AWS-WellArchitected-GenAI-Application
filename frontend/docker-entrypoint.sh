#!/bin/sh

# Replace runtime config with actual environment variable
if [ -n "$NEXT_PUBLIC_API_URL" ]; then
  echo "Setting NEXT_PUBLIC_API_URL to: $NEXT_PUBLIC_API_URL"
  sed -i "s|__NEXT_PUBLIC_API_URL__|$NEXT_PUBLIC_API_URL|g" /app/public/runtime-config.js
else
  echo "Warning: NEXT_PUBLIC_API_URL not set, using default"
  sed -i "s|__NEXT_PUBLIC_API_URL__|http://localhost:8000|g" /app/public/runtime-config.js
fi

# Start the application
exec node server.js
