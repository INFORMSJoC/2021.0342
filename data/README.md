

This directory consists of data instances and raw results of the paper. 
The directory is organized by number of linacs and arrival rate (lambda) using the tree structure as follows

```bash
.
├── 4linacs
│   ├── lambda5.0
│   │  ├── data ( data instances)
│   │  └── output
│   │      ├── prediction   (raw testing/training csv files and the trained regression model)
│   │      └── results      (detailed results of data instances)
│   └── lambda6.0
│      ├── ...
├── ....
├── 8linacs
│   ├── lambda10.0...
│   └── lambda12.0...
└── real_ins         
    ├── results         (raw result)
    └── realins.csv     (instance file)
```