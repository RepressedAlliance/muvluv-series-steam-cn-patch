"""Add the local runtime import and wait for initialization before native entry.

Build dependency: LIEF 0.17.6. No original game executable is redistributed;
the package builder emits a version-checked delta for the installer instead.
"""
import hashlib
import struct


def embed_runtime(original: bytes) -> tuple[bytes, dict]:
    import lief
    import pefile
    parsed=pefile.PE(data=original)
    if parsed.FILE_HEADER.Machine != 0x8664:
        raise ValueError('Only the supported x64 game executables are accepted')
    if any(s.Name.rstrip(b'\0') == b'.cnload' for s in parsed.sections):
        raise ValueError('Runtime is already embedded')
    imports={entry.name:entry.address-parsed.OPTIONAL_HEADER.ImageBase
             for library in parsed.DIRECTORY_ENTRY_IMPORT for entry in library.imports}
    required=(b'Sleep',b'ExitProcess',b'MessageBoxW')
    if not all(name in imports for name in required):
        raise ValueError('Required native Windows imports are missing')
    pe=lief.PE.parse(original)
    pe.add_import('FridaGadget.dll').add_entry('frida_gadget_config_get_type')
    state=lief.PE.Section('.cnstate');state.content=[0]*16;state.characteristics=0xc0000040
    flag=pe.add_section(state).virtual_address
    section=lief.PE.Section('.cnload');section.content=[0]*1024;section.characteristics=0x60000020
    code_section=pe.add_section(section);start=code_section.virtual_address
    code=bytearray();labels={};fixups=[]
    def emit(data):code.extend(bytes.fromhex(data))
    def mark(name):labels[name]=start+len(code)
    def relative(prefix,target):
        emit(prefix);fixups.append((len(code),target));code.extend(b'\0'*4)
    # Preserve entry registers and flags, and keep Windows x64 stack alignment.
    emit('9c 50 51 52 41 50 41 51 41 52 41 53 41 54 48 83 ec 20')
    emit('41 bc b8 0b 00 00')  # 3000 * 10 ms, then fail visibly.
    mark('wait');relative('80 3d',flag);emit('01')
    # cmp's displacement is relative to the byte after its immediate operand.
    fixups[-1]=(fixups[-1][0],flag-1)
    relative('0f 84','resume')
    emit('b9 0a 00 00 00');relative('ff 15',imports[b'Sleep'])
    emit('41 ff cc');relative('0f 85','wait')
    emit('31 c9');relative('48 8d 15','error');relative('4c 8d 05','title')
    emit('41 b9 10 00 00 00');relative('ff 15',imports[b'MessageBoxW'])
    emit('b9 01 00 00 00');relative('ff 15',imports[b'ExitProcess']);emit('cc')
    mark('resume');emit('48 83 c4 20 41 5c 41 5b 41 5a 41 59 41 58 5a 59 58 9d')
    relative('e9',parsed.OPTIONAL_HEADER.AddressOfEntryPoint)
    mark('title');code.extend('AGE2 中文补丁\0'.encode('utf-16-le'))
    mark('error');code.extend('中文运行组件初始化失败。请重新安装补丁，或使用卸载程序恢复原版。\0'.encode('utf-16-le'))
    for offset,target in fixups:
        destination=labels[target] if isinstance(target,str) else target
        struct.pack_into('<i',code,offset,destination-(start+offset+4))
    code_section.content=list(code)
    pe.optional_header.addressof_entrypoint=start
    options=lief.PE.Builder.config_t();options.imports=True
    result=pe.write_to_bytes(options)
    changed=pefile.PE(data=result)
    for section in parsed.sections:
        if section.Characteristics & 0x20000000:
            if parsed.get_data(section.VirtualAddress,section.Misc_VirtualSize)!=changed.get_data(section.VirtualAddress,section.Misc_VirtualSize):
                raise ValueError(f'Original code changed: {section.Name}')
    def iat(image):
        return {entry.address:(library.dll,entry.name,entry.ordinal)
                for library in image.DIRECTORY_ENTRY_IMPORT for entry in library.imports}
    before,after=iat(parsed),iat(changed)
    if not all(after.get(address)==record for address,record in before.items()):
        raise ValueError('An original IAT address changed')
    return result,{'original_sha256':hashlib.sha256(original).hexdigest(),
                   'patched_sha256':hashlib.sha256(result).hexdigest(),
                   'ready_rva':flag,'loader_rva':start,
                   'native_entry_rva':parsed.OPTIONAL_HEADER.AddressOfEntryPoint,
                   'original_iat_preserved':len(before),
                   'original_executable_sections_preserved':True}
