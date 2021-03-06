#!/usr/bin/env python

"""
Parses the output of sizer.exe.
"""

g_file_name = "efi_out.txt"

(SECTION_CODE, SECTION_DATA, SECTION_BSS, SECTION_UNKNOWN) = ("C", "D", "B", "U")

# maps a numeric string idx to string. We take advantage of the fact that
# strings in efi.exe output are stored with consequitive indexes so can use
#
class Strings():

	def __init__(self):
		self.strings = []

	def add(self, idx, str):
		assert idx == len(self.strings)
		self.strings.append(str)

	def idx_to_str(self, idx):
		return self.strings[idx]

# type | sectionNo | length | offset | objFileId
# C|1|35|0|C:\Users\kkowalczyk\src\sumatrapdf\obj-dbg\sumatrapdf\SumatraPDF.obj
class Section(object):
	def __init__(self, l):
		parts = l.split("|")
		assert len(parts) == 5
		self.type = parts[0]
		self.section_no = int(parts[1])
		self.size = int(parts[2])
		self.offset = int(parts[3])
		# it's either name id in compact mode or full name
		self.name = parts[4]

(SYM_NULL, SYM_EXE, SYM_COMPILAND, SYM_COMPILAND_DETAILS) = ("N", "Exe", "C", "CD")
(SYM_COMPILAND_ENV, SYM_FUNCTION, SYM_BLOCK, SYM_DATA) = ("CE", "F", "B", "D")
(SYM_ANNOTATION, SYM_LABEL, SYM_PUBLIC, SYM_UDT, SYM_ENUM) = ("A", "L", "P", "U", "E")
(SYM_FUNC_TYPE, SYM_POINTER_TYPE, SYM_ARRAY_TYPE) = ("FT", "PT", "AT")
(SYM_BASE_TYPE, SYM_TYPEDEF, SYM_BASE_CLASS, SYM_FRIEND) = ("BT", "T", "BC", "Friend")
(SYM_FUNC_ARG_TYPE, SYM_FUNC_DEBUG_START, SYM_FUNC_DEBUG_END) = ("FAT", "FDS", "FDE")
(SYM_USING_NAMESPACE, SYM_VTABLE_SHAPE, SYM_VTABLE, SYM_CUSTOM) = ("UN", "VTS", "VT", "Custom")
(SYM_THUNK, SYM_CUSTOM_TYPE, SYM_MANAGED_TYPE, SYM_DIMENSION) = ("Thunk", "CT", "MT", "Dim")

# type | section | length | offset | rva | name
# F|1|35|0|4096|AllocArray<wchar_t>|wchar_t*__cdeclAllocArray<wchar_t>(unsignedint)
class Symbol(object):
	def __init__(self, l):
		parts = l.split("|")
		assert len(parts) == 6, "len(parts) is %d\n'%s'" % (len(parts), l)
		self.type = parts[0]
		self.section = int(parts[1])
		self.size = int(parts[2])
		self.offset = int(parts[3])
		self.rva = int(parts[4])
		self.name = parts[5]

class Type(object):
	def __init__(self, l):
		# TODO: parse the line
		self.line = l

class ParseState(object):
	def __init__(self, fo):
		self.fo = fo
		self.strings = Strings()
		self.types = []
		self.symbols = []
		self.sections = []

	def readline(self):
		l = self.fo.readline()
		if not l:
			return None
		l = l.rstrip()
		#print("'%s'" % l)
		return l

def parse_start(state):
	l = state.readline()
	assert l == "Format: 1", "unexpected line: '%s'" % l
	return parse_next_section

def parse_next_section(state):
	l = state.readline()
	#print("'%s'" % l)
	if l == None: return None
	if l == "": return parse_next_section
	if l == "Strings:":
		return parse_strings
	if l == "Types:":
		return parse_types
	if l == "Sections:":
		return parse_sections
	if l == "Symbols:":
		return parse_symbols
	print("Unknonw section: '%s'" % l)
	return None

def parse_strings(state):
	while True:
		l = state.readline()
		if l == None: return None
		if l == "": return parse_next_section
		parts = l.split("|", 2)
		idx = int(parts[0])
		state.strings.add(idx, parts[1])

def parse_sections(state):
	while True:
		l = state.readline()
		if l == None: return None
		if l == "": return parse_next_section
		state.sections.append(Section(l))

def parse_symbols(state):
	while True:
		l = state.readline()
		if l == None: return None
		if l == "": return parse_next_section
		state.symbols.append(Symbol(l))

def parse_types(state):
	while True:
		l = state.readline()
		if l == None: return None
		if l == "": return parse_next_section
		# TODO: should parse structs, not just count them
		if l.startswith("struct"):
			state.types.append(Type(l))

def parse_file_object(fo):
	curr = parse_start
	state = ParseState(fo)
	while curr:
		curr = curr(state)
	return state

def parse_file(file_name):
	print("parse_file: %s" % file_name)
	with open(file_name, "r") as fo:
		return parse_file_object(fo)

class Diff(object):
	def __init__(self):
		self.added = []
		self.removed = []
		self.changed = []
		self.str_sizes_diff = 0

	def __repr__(self):
		s = "%d added\n%d removed\n%d changed\n%d string sizes diff" % (len(self.added), len(self.removed), len(self.changed), self.str_sizes_diff)
		return s

def same_sym_sizes(syms):
	sizes = []
	for sym in syms:
		if sym.size in sizes:
			return True
		sizes.append(sym.size)
	return False

# Unfortunately dia2 sometimes doesn't give us unique names for functions,
# so we need to
class DiffSyms(object):
	def __init__(self):
		self.name_to_sym = {}
		self.dup_syms = []
		self.str_sizes = 0

	def process_symbols(self, symbols):
		for sym in symbols:
			name = sym.name
			# for anonymous strings, we just count their total size
			# since we don't have a way to tell one string from another
			if name == "*str":
				self.str_sizes += sym.size
				continue

			if name not in self.name_to_sym:
				self.name_to_sym[name] = sym
				continue
			self.dup_syms.append(sym)
		# some dup symbols are still pointed to by self.name_to_sym
		for sym in self.dup_syms:
			name = sym.name
			if name in self.name_to_sym:
				dup_sym = self.name_to_sym[name]
				self.dup_syms.append(dup_sym)
				del self.name_to_sym[name]

		# create unique names for dup symbols
		for sym in self.dup_syms:
			name = self.sym_name(sym)
			assert name not in self.name_to_sym, "%s should be unique" % name
			self.name_to_sym[name] = sym

	def sym_name(self, sym):
		# uniquify the name by appending its size to the name. If sizes are
		# the same, append offset
		syms = [s for s in self.dup_syms if s.name == sym.name]
		assert len(syms) > 1
		if same_sym_sizes(syms):
			return "%s_%d" % (sym.name, sym.offset)
		else:
			return "%s_%d" % (sym.name, sym.size)

def diff(parse1, parse2):
	assert isinstance(parse1, ParseState)
	assert isinstance(parse2, ParseState)
	diff_syms1 = DiffSyms()
	diff_syms1.process_symbols(parse1.symbols)

	diff_syms2 = DiffSyms()
	diff_syms2.process_symbols(parse2.symbols)

	added = []
	changed = []

	removed_from1_names = {}
	for name in diff_syms1.name_to_sym.keys():
		removed_from1_names[name] = True

	for name in diff_syms2.name_to_sym.keys():
		if name not in diff_syms1.name_to_sym:
			added.append(diff_syms2.name_to_sym[name])
		else:
			sym1 = diff_syms1.name_to_sym[name]
			sym2 = diff_syms2.name_to_sym[name]
			if sym1.size != sym2.size:
				changed += [sym1]
			# we remove those we've seen so that at the end the only symbols
			# left in symbols1 are those that were removed (i.e. not present in symbols2)
			del removed_from1_names[name]

	removed = [diff_syms1.name_to_sym[k] for k in removed_from1_names.keys()]
	diff = Diff()
	diff.added = added
	diff.removed = removed
	diff.changed = changed
	diff.str_sizes_diff = diff_syms1.str_sizes - diff_syms2.str_sizes
	return diff

def main():
	state = parse_file(g_file_name)
	print("%d types, %d sections, %d symbols" % (len(state.types), len(state.sections), len(state.symbols)))

if __name__ == "__main__":
	main()
