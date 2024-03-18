# Gazepoint gives coordinates as a fraction. While the documents say 0,0 is
# the top left and 1,1 is the bottom right, in reality it seems to squish
# everything into a square with sides the same as the screen height.
def fraction_to_pixel(x_frac, y_frac, width, height):
    x_px = int(round((((x_frac - 0.5) * (width / height)) + 0.5) * width))
    y_px = int(round(y_frac * height)) 

    return (x_px, y_px)

# EOF
