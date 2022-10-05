import setuptools

with open("requirements.txt", "r", encoding="utf-8") as f:
    install_requires = f.read().splitlines()

setuptools.setup(
    name="resolve-toolkits",
    packages=["resolve_toolkits"],
    install_requires=install_requires,
)
