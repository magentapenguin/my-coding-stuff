svg = input("SVG: ")
symid = input("ID: ")
print("<svg class=\"go-away\">"+svg.replace("<svg", f"<symbol id={symid}").replace("</svg>", "</symbol>")+ "</svg>")