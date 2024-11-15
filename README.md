# Tools

- `batch_mount_smbfs.py`: Mount multiple SMB drives at once.
- `dummy_dirs.py`: Create dummy directories to mimic the structure and files of the
  source directory.
- `get_dctl_node.py`: Script to check clips in track 1 of current timeline for DCTL tool
  usage.
- `get_remote_version.py`: Script to check clips in current timeline with remote
  versions.
- `modification_time.py`: Retrieve modification time of files.
- `source_proxy_num_checker.py`: Check if the files in the source footage folder
  correspond one-to-one with the files in the proxy folder.

---

`get_dctl_node.py` sample output:

```sh
$ python3 src/get_dctl_node.py
The following clips in timeline "main" have DCTL tool used:

  Clip Number  Clip Name                 Node Index    Node Label
-------------  ------------------------  ------------  -----------------
           12  A001C005_130101_R2U8.mov  [10]          ['tetra']
           14  A001C015_130101_R2U8.mov  [9]           ['split tone']
           16  A001C008_130101_R2U8.mov  [20, 22]      ['', '']
           18  A001C002_130101_R2U8.mov  [12]          ['tetra']
           19  A001C015_130101_R2U8.mov  [9]           ['split tone']
           20  A001C002_130101_R2U8.mov  [12]          ['tetra']
...
```

To make the script work better, **please label all DCTL nodes (at least the ones that use the DCTL tool)**. If not, you can see that the node label column above outputs useless '' strings, so much so that even after running this script (to get which DCTL is used for which node), you still don't know which DCTL is used here.

---

Based on the current implementation of `render_exr.py`, here's what the user needs to do before running it:

1. Add the marker on the current timeline (Blue marker only).
2. Go to the Color Page and manually convert the current clip color space to ACES AP0/Linear. `render_exr.py` will automatically set the timeline to the desired settings.
