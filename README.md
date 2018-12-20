# Tral Visualization

Code for visualizing TRAL results.

# Installation

```
python setup.py install
```

The code is intended to be used with jupyter notebooks.

# Usage

For usage, see the example [Jupyter notebook](repeatdiagram%20usage.ipynb). Unfortunately, github removes HTML formatting from results due to security conserns, so `show_hmm_state` output is not displayed correctly.

In brief, two types of output are supported. The `RepeatDiagram` class is used for visualizing TRAL RepeatList objects on one or more sequences.

![RepeatDiagram Example](docs/repeatdiagram.png)

The `show_hmm_state` function maps more detailed information about each repeat. It requires that each residue of a sequence be annotated with the repeat state.

Compact representation:
![show_hmm_state Example 1](docs/show_hmm_state1.png)

Detailed representation:
![show_hmm_state Example 2](docs/show_hmm_state2.png)
