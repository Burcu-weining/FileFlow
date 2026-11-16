from converter import convert_image

print ("Welcome to FileFlow!")

input_file = input("Enter the file name: ")
output_format = input("Convert to (JPG/PNG/WEBP): ")

try:
    output = convert_image(input_file, output_format)
    print("conversion successful!")
    print("Saved to:", output)
    
except Exception as error:
    print("Conversion failed:", error)
