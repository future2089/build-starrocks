import zipfile, sys
jar_path = sys.argv[1]
class_path = sys.argv[2]
out_dir = sys.argv[3]
z = zipfile.ZipFile(jar_path)
z.extract(class_path, out_dir)
z.close()
print("EXTRACTED")
