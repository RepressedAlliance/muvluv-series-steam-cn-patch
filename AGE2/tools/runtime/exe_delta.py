"""Small, version-checked executable deltas; never package the original EXE."""
import base64
import hashlib


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def make_delta(original: bytes, patched: bytes) -> dict:
    edits=[];index=0
    while index<len(patched):
        if index<len(original) and original[index]==patched[index]:
            index+=1;continue
        start=index;last=index
        while index<len(patched):
            if index>=len(original) or original[index]!=patched[index]:last=index
            elif index-last>24:break
            index+=1
        end=last+1
        edits.append({'offset':start,'data':base64.b64encode(patched[start:end]).decode('ascii')})
    result={'format':'age2-exe-delta-1','original_sha256':digest(original),
            'patched_sha256':digest(patched),'output_size':len(patched),'edits':edits}
    if apply_delta(original,result)!=patched:raise AssertionError('Delta round trip failed')
    return result


def apply_delta(original: bytes, delta: dict) -> bytes:
    if delta.get('format')!='age2-exe-delta-1' or digest(original)!=delta['original_sha256']:
        raise ValueError('Unsupported game version or invalid delta')
    size=delta['output_size']
    if not isinstance(size,int) or size<1 or size>256*1024*1024:
        raise ValueError('Invalid executable size')
    result=bytearray(size);result[:min(size,len(original))]=original[:size]
    previous_end=0
    for edit in delta['edits']:
        offset=edit['offset'];data=base64.b64decode(edit['data'],validate=True)
        if not isinstance(offset,int) or offset<previous_end or offset+len(data)>size:
            raise ValueError('Overlapping or out-of-range delta')
        result[offset:offset+len(data)]=data;previous_end=offset+len(data)
    if digest(result)!=delta['patched_sha256']:
        raise ValueError('Patched executable verification failed')
    return bytes(result)
