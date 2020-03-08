run: 
	python3 src/resolver.py $(PORT)
pack:
	zip -r xsovam00.zip makefile src/ readme.md
