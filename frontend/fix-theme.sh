#!/bin/bash

# Fix white text on white background issue across all components

# Function to replace color values
fix_colors() {
  local file=$1
  echo "Fixing colors in $file"

  # Fix background colors
  sed -i 's/background: rgba(255, 255, 255, 0.1)/background: #ffffff/g' "$file"
  sed -i 's/backdrop-filter: blur(10px);//g' "$file"
  sed -i 's/border: 1px solid rgba(255, 255, 255, 0.2)/border: 1px solid #e2e8f0/g' "$file"

  # Fix text colors
  sed -i 's/color: white;/color: #0f172a;/g' "$file"
  sed -i 's/color: rgba(255, 255, 255, 0.7)/color: #64748b/g' "$file"
  sed -i 's/color: rgba(255, 255, 255, 0.8)/color: #475569/g' "$file"
  sed -i 's/color: rgba(255, 255, 255, 0.6)/color: #94a3b8/g' "$file"

  # Add box shadow to cards
  sed -i 's/border-radius: 12px;/border-radius: 12px;\n  box-shadow: 0 1px 3px 0 rgb(0 0 0 \/ 0.1);/g' "$file"
}

# Fix all component files
for file in src/components/*.js src/pages/*.js; do
  if [ -f "$file" ]; then
    fix_colors "$file"
  fi
done

echo "Theme fix complete!"