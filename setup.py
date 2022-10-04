import setuptools

with open("requirements.txt", "r") as f:
    install_requires = f.read().splitlines()

setuptools.setup(
    name="resolve-toolkits",
    packages=["resolve-toolkits"],
    install_requires=install_requires,
)
