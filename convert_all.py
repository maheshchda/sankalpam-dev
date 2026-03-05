import fitz  # PyMuPDF
import os

def convert_pdfs_to_text(directory):
    # Ensure the path is absolute and uses correct slashes
    target_dir = os.path.abspath(directory)
    
    # Check if directory exists
    if not os.path.exists(target_dir):
        print(f"Error: The folder {target_dir} was not found.")
        return

    # Loop through all files in the directory
    for filename in os.listdir(target_dir):
        if filename.lower().endswith(".pdf"):
            pdf_path = os.path.join(target_dir, filename)
            txt_filename = os.path.splitext(filename)[0] + ".txt"
            txt_path = os.path.join(target_dir, txt_filename)
            
            print(f"Converting: {filename}...")
            
            try:
                # Open the PDF
                with fitz.open(pdf_path) as doc:
                    text = ""
                    for page in doc:
                        # 'get_text' preserves the layout and character integrity
                        text += page.get_text()
                
                # Write to text file using UTF-8 to prevent data loss
                with open(txt_path, "w", encoding="utf-8") as f:
                    f.write(text)
                    
                print(f"Successfully saved to: {txt_filename}")
            
            except Exception as e:
                print(f"Failed to convert {filename}: {e}")

# Run the function for your specific path
if __name__ == "__main__":
    folder_path = r"C:\Projects\sankalpam-dev"
    convert_pdfs_to_text(folder_path)