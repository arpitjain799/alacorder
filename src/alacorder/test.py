from alacorder import alac
import pandas as pd
def append(in_path, out_path, no_write=False):

    input_archive = alac.read(in_path)
    print(input_archive)
    output_archive = alac.read(out_path)
    print(output_archive)
    new_archive = pd.concat([output_archive, input_archive], ignore_index=True)
    print(new_archive)
    if not no_write:
        cin = alac.setinputs(input_archive)
        cout = alac.setoutputs(out_path)
        conf = alac.set(cin, cout)
        alac.write(conf, new_archive)

    return new_archive