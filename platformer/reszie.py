from PIL import Image

def resize_image(image_path, output_path, size):
    original_image = Image.open(image_path)
    # Remove colors "FF00DC" and "00FF21"
    original_image = original_image.convert("RGBA")
    pixels = original_image.load()
    width, height = original_image.size
    for y in range(height):
        for x in range(width):
            r, g, b, a = pixels[x, y]
            if (r, g, b) == (255, 0, 220) or (r, g, b) == (0, 255, 33):
                pixels[x, y] = (0, 0, 0, 0)
    width, height = original_image.size
    print('The original image size is: ', width, height)
    resized_image = original_image.resize(size, Image.BOX)
    width, height = resized_image.size
    print('The resized image size is: ', width, height)
    resized_image.save(output_path)


if __name__ == '__main__':
    image_path = './sprites/steel.png'
    output_path = './sprites/steelr.png'
    size = (16*4, 16*4)
    resize_image(image_path, output_path, size)