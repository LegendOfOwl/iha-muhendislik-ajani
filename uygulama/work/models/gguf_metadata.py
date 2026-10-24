"""Read selected GGUF metadata without loading tensors or executing model code."""
import struct
def read_metadata(path):
    with open(path,'rb') as f:
        def unpack(fmt): return struct.unpack('<'+fmt,f.read(struct.calcsize('<'+fmt)))[0]
        def string(keep=True):
            n=unpack('Q')
            if keep: return f.read(n).decode('utf-8',errors='replace')
            f.seek(n,1)
        sizes={0:'B',1:'b',2:'H',3:'h',4:'I',5:'i',6:'f',7:'?',10:'Q',11:'q',12:'d'}
        def value(kind,keep=True):
            if kind==8: return string(keep)
            if kind==9:
                subtype=unpack('I'); count=unpack('Q')
                if not keep and subtype in sizes: f.seek(count*struct.calcsize('<'+sizes[subtype]),1); return None
                if keep: return [value(subtype,True) for _ in range(count)]
                for _ in range(count): value(subtype,False)
                return None
            if kind not in sizes: raise ValueError('Unknown GGUF metadata type')
            return unpack(sizes[kind])
        assert f.read(4)==b'GGUF'
        version=unpack('I'); tensors=unpack('Q'); kv=unpack('Q')
        result={'gguf_version':version,'tensor_count':tensors,'kv_count':kv}
        for _ in range(kv):
            key=string(); kind=unpack('I')
            keep=key.startswith('general.') or key in {'tokenizer.chat_template','tokenizer.ggml.bos_token_id','tokenizer.ggml.eos_token_id','tokenizer.ggml.add_bos_token','tokenizer.ggml.add_eos_token'}
            item=value(kind,keep)
            if keep: result[key]=item
        return result
