# src/aura_core/apprentices/image_finder.py
import os
import requests
from ddgs import DDGS # Use the updated library name
import traceback

def run(payload):
    """
    Searches for images online with advanced filters, downloads them, and saves locally.
    Returns a list of saved file paths.
    """
    query = payload.get("query")
    filename_base = payload.get("filename") # Can be a full path "img.png" or a base "img"
    max_results = int(payload.get("max_results", 1))

    # Advanced filters
    safesearch = payload.get("safesearch", "moderate") # "on", "moderate", "off"
    size = payload.get("size") # "Small", "Medium", "Large", "Wallpaper"
    color = payload.get("color") # e.g., "red", "blackandwhite"
    type_image = payload.get("type_image") # "photo", "clipart", "gif", "transparent"
    license_image = payload.get("license_image") # "any", "creative_commons", "public_domain"
    
    if not query:
        return "Error: Missing 'query' for image search."
    if not filename_base:
        return "Error: Missing 'filename' (local path base) to save the image(s)."

    try:
        print(f"--- Image Finder: Searching for {max_results} image(s) for '{query}' ---")
        
        # Map simple names to DDGS names
        license_map = {
            "creative_commons": "creativeCommon",
            "public_domain": "publicDomain",
            "any": "any",
        }
        ddgs_license = license_map.get(str(license_image).lower())

        image_urls = []
        with DDGS() as ddgs:
            results = list(ddgs.images(
                query,
                max_results=max_results,
                safesearch=safesearch,
                size=size,
                color=color,
                type_image=type_image,
                license_image=ddgs_license
            ))
            
            if results:
                image_urls = [r.get('image') for r in results]

        if not image_urls:
            return f"Error: No image results found for '{query}' with the specified filters."

        print(f"--- Image Finder: Found {len(image_urls)} image URL(s). Downloading... ---")

        # --- Smart File Path Handling ---
        # "logo.png" -> dir=".", base="logo", ext=".png"
        # "images/logo.png" -> dir="images", base="logo", ext=".png"
        # "images/logo" -> dir="images", base="logo", ext="" (will be added)
        img_dir = os.path.dirname(filename_base)
        base_name, ext = os.path.splitext(os.path.basename(filename_base))
        if not ext:
            ext = ".jpg" # Default to .jpg if no extension provided

        # Ensure directory exists
        if img_dir and not os.path.exists(img_dir):
            os.makedirs(img_dir, exist_ok=True)
            print(f"--- Image Finder: Created destination directory '{img_dir}' ---")

        saved_files = []
        for i, url in enumerate(image_urls):
            if not url:
                continue
                
            # Create unique filename for multiple results
            if max_results > 1:
                current_filename = os.path.join(img_dir, f"{base_name}_{i+1:02d}{ext}")
            else:
                current_filename = os.path.join(img_dir, f"{base_name}{ext}")

            try:
                # Download the image
                response = requests.get(url, stream=True, timeout=15)
                response.raise_for_status()

                # Save the image
                with open(current_filename, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                print(f"--- Image Finder: Successfully downloaded '{current_filename}' ---")
                saved_files.append(current_filename)

            except requests.exceptions.RequestException as req_e:
                print(f"--- Image Finder Warning: Failed to download image from {url}. Reason: {req_e} ---")
            except Exception as e_file:
                 print(f"--- Image Finder Warning: Failed to save file '{current_filename}'. Reason: {e_file} ---")

        if not saved_files:
             return "Error: Found image URLs, but failed to download any of them."

        # Return a single path (string) if only one image was requested and found
        if len(saved_files) == 1:
            return saved_files[0]
            
        # Return a list of paths if multiple images were saved
        return saved_files

    except Exception as e:
        print(traceback.format_exc()) # Print detailed error
        return f"Error finding or saving image for '{query}'. Reason: {e}"