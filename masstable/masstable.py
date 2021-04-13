# -*- coding: utf-8 -*-
from __future__ import annotations

import pandas as pd
import os
import math
import functools
from functools import wraps
from typing import Callable, List, Tuple

package_dir, _ = os.path.split(__file__)


def memoize(obj):
    cache = obj.cache = {}

    @functools.wraps(obj)
    def memoizer(*args, **kwargs):
        key = str(args) + str(kwargs)
        if key not in cache:
            cache[key] = obj(*args, **kwargs)
        return cache[key]

    return memoizer


class Table:
    def __init__(self, name: str = "", df: pd.DataFrame = None):
        "Init from a Series/Dataframe (df) of a file (name)"
        if df is not None:  # init from dataframe
            self.df = df
            self.name = name
        elif name in self._names:  # init from name
            self.name = name
            self.df = self.from_name(name).df
            # self.df.name = name
        else:
            print("Error: Invalid table name. Valid names are:")
            print(" ".join(Table.names))
            return None

    _names = [
        "AME2003",
        "AME2003all",
        "AME2012",
        "AME2012all",
        "AME1995",
        "AME1995all",
        "DUZU",
        "FRDM95",
        "KTUY05",
        "ETFSI12",
        "HFB14",
        "HFB26",
        "TCSM12",
        "TCSM13",
        "BR2013",
        "MAJA88",
        "GK88",
        "WS32010",
        "WS32011",
        "SVM13",
    ]

    @classmethod
    def names(cls):
        """Return a list of the names of all supported mass models

        Example:

            >>> Table.names()
            ['AME2003', 'AME2003all', 'AME2012', 'AME2012all', 'AME1995',
            'AME1995all', 'DUZU', 'FRDM95', 'KTUY05', 'ETFSI12', 'HFB14',
            'HFB26', 'TCSM12', 'TCSM13', 'BR2013', 'MAJA88', 'GK88', 'WS32010', 'WS32011',
            'SVM13']
        """
        return cls._names

    @classmethod
    def from_name(cls, name: str):
        "Imports a mass table from a file"
        filename = os.path.join(package_dir, "data", name + ".txt")
        return cls.from_file(filename, name)

    @classmethod
    def from_file(cls, filename: str, name: str = ""):
        "Imports a mass table from a file"

        df = pd.read_csv(filename, header=0, delim_whitespace=True, index_col=[0, 1])[
            "M"
        ]
        df.name = name
        return cls(df=df, name=name)

    @classmethod
    def from_ZNM(cls, Z, N, M, name=""):
        """
        Creates a table from arrays Z, N and M

        Example:
        ________

            >>> Z = [82, 82, 83]
            >>> N = [126, 127, 130]
            >>> M = [-21.34, -18.0, -14.45]
            >>> Table.from_ZNM(Z, N, M, name='Custom Table')
            Z   N
            82  126   -21.34
                127   -18.00
            83  130   -14.45
            Name: Custom Table, dtype: float64
        """
        df = pd.DataFrame.from_dict({"Z": Z, "N": N, "M": M}).set_index(["Z", "N"])["M"]
        df.name = name
        return cls(df=df, name=name)

    @classmethod
    def from_array(cls, arr, name=""):
        Z, N, M = arr.T
        return cls.from_ZNM(Z, N, M, name)

    def to_file(self, path: str):
        """Export the contents to a file as comma separated values.

        Parameters:
            path : File path where the data should be saved to

        Example:
            Export the last ten elements of AME2012 to a new file:

                >>> Table('AME2012').tail(10).to_file('last_ten.txt')
        """
        with open(path, "w") as f:
            f.write("Z   N   M\n")
        self.df.to_csv(path, sep="\t", mode="a")

    @property
    def Z(self):
        """
        Return the proton number Z for all nuclei in the table as a numpy array.
        """
        return self.df.index.get_level_values("Z").values

    @property
    def N(self):
        """
        Return the neutron number N for all nuclei in the table as a numpy array.
        """
        return self.df.index.get_level_values("N").values

    @property
    def A(self):
        """
        Return the mass number A for all nuclei in the table as a numpy array.
        """
        return self.Z + self.N

    def __getitem__(self, index):
        """Access [] operator

        Examples
        --------

            >>> Table('DUZU')[82, 126:127]
            DUZU
            Z   N
            82  126 -22.29
                127 -17.87

            >>> Table('AME2012all')[118, :]
            AME2012all
            Z   N
            118 173  198.93
                174  199.27
                175  201.43

        """
        if isinstance(index, tuple) and len(index) == 2:
            # can probably be simplified with pd.IndexSlice
            if isinstance(index[0], int):  # single N: "[82, :]"
                startZ, stopZ = index[0], index[0]

            if isinstance(index[1], int):
                startN, stopN = index[1], index[1]  # single N: "[:, 126]"

            if isinstance(index[0], slice):  # Z slice: "[:, 126]"
                startZ, stopZ, stepZ = index[0].start, index[0].stop, index[0].step

            if isinstance(index[1], slice):  # N slice: "[:, 126]"
                startN, stopN, stepN = index[1].start, index[1].stop, index[1].step

            if not startZ:
                startZ = self.Z.min()  # might be optimized
            if not stopZ:
                stopZ = self.Z.max()
            if not startN:
                startN = self.N.min()
            if not stopN:
                stopN = self.N.max()

            x = self.df.reset_index()
            x = x.loc[
                (x.Z >= startZ) & (x.Z <= stopZ) & (x.N >= startN) & (x.N <= stopN)
            ]
            df = x.set_index(["Z", "N"]).sort_index(0)
            return Table(df=df[df.columns[0]], name=self.name)

        if isinstance(index, list):
            return self.at(index)

        if isinstance(index, Callable):
            return self.select(index)

    def __setitem__(self, key: int, value: int) -> None:
        Z = key[0]
        N = key[1]
        self.df.loc[(Z, N)] = value

    def __getattr__(self, attr):
        # TODO: Pythonize
        "Pass properties and method calls to the DataFrame object"
        instance_method = getattr(self.df, attr)
        if callable(instance_method):

            def fn(*args, **kwargs):
                result = instance_method(
                    *args, **kwargs
                )  # ()->call the instance method
                if isinstance(result, (pd.DataFrame, pd.Series)):
                    try:
                        name = result.name
                    except AttributeError:
                        name = None
                    return Table(name=name, df=result)  # wrap in Table class

            return fn
        else:
            return instance_method

    def __iter__(self):
        for e in self.df.iteritems():
            yield e

    def __add__(self, other):
        return Table(df=self.df + other.df, name="{}+{}".format(self.name, other.name))

    def __sub__(self, other):
        return Table(df=self.df - other.df, name="{}+{}".format(self.name, other.name))

    def __div__(self, other):
        return Table(df=self.df - other.df, name="{}+{}".format(self.name, other.name))

    def align(self, *args, **kwargs):
        result = self.df.align(*args, **kwargs)[0]
        return Table(result.name, result)

    def select(self, condition: Callable, name: str = "") -> Table:
        """
        Selects nuclei according to a condition on Z,N or M

        Parameters:

            condition:
                Can have one of the signatures f(M), f(Z,N) or f(Z, N, M)
                must return a boolean value
            name:
                optional name for the resulting Table

        Example:

            Select all nuclei with A > 160:

                >>> A_gt_160 = lambda Z,N: Z + N > 160
                >>> Table('AME2003').select(A_gt_160)
        """
        if condition.__code__.co_argcount == 1:
            idx = [(Z, N) for (Z, N), M in self if condition(M)]
        if condition.__code__.co_argcount == 2:
            idx = [(Z, N) for (Z, N) in self.index if condition(Z, N)]
        if condition.__code__.co_argcount == 3:
            idx = [(Z, N) for (Z, N), M in self if condition(Z, N, M)]
        index = pd.MultiIndex.from_tuples(idx, names=["Z", "N"])
        return Table(df=self.df.loc[index], name=name)

    def at(self, nuclei: List[Tuple[int, int]]) -> Table:
        """Return a selection of the Table at positions given by ``nuclei``

        Parameters:

            nuclei: list of tuples
                A list where each element is tuple of the form (Z,N)

        Example
        -------
        Return binding energies at magic nuclei:

            >>> magic_nuclei = [(20,28), (50,50), (50,82), (82,126)]
            >>> Table('AME2012').binding_energy.at(magic_nuclei)
            Z   N
            20  28      416.014215
            50  50      825.325172
                82     1102.876416
            82  126    1636.486450
        """
        index = pd.MultiIndex.from_tuples(nuclei, names=["Z", "N"])
        return Table(df=self.df.loc[index], name=self.name)

    @classmethod
    def empty(cls, name: str = "") -> Table:
        return cls(df=pd.DataFrame(index=[], columns=[]), name=name)

    def __len__(self):
        """Return the total number of nuclei

        Example
        -------

            >>> len(Table('AME2012'))
            2438
        """
        return len(self.df)

    @property
    def count(self) -> int:
        """Return the total number of nuclei in the table

        Example:

            >>> Table('AME2012').count
            2438

        It is also possible to do:

            >>> len(Table('AME2012'))
            2438
        """
        return len(self.df)

    def intersection(self, table: Table) -> Table:
        """
        Select nuclei which also belong to ``table``

        Parameters:

            table: a Table object

        Example
        -------

            >>> Table('AME2003').intersection(Table('AME1995'))
        """
        idx = self.df.index.intersection(table.df.index)
        return Table(df=self.df[idx], name=self.name)

    def not_in(self, table: Table) -> Table:
        """
        Select nuclei not in table

        Parameters:

            table: Table
                Table object from where nuclei should be removed

        Example
        -------
        Find the new nuclei in AME2003 with Z,N >= 8:

            >>> Table('AME2003').not_in(Table('AME1995'))[8:,8:].count
            389
        """
        idx = self.df.index.difference(table.df.index)
        return Table(df=self.df[idx], name=self.name)

    @property
    @memoize
    def odd_odd(self):
        """Selects odd-odd nuclei from the table:

            >>> Table('FRDM95').odd_odd
            Z   N
            9   9       1.21
                11      0.10
                13      3.08
                15      9.32
        ...
        """
        return self.select(lambda Z, N: (Z % 2) and (N % 2), name=self.name)

    @property
    @memoize
    def odd_even(self) -> Table:
        """
        Selects odd-even nuclei from the table
        """
        return self.select(lambda Z, N: (Z % 2) and not (N % 2), name=self.name)

    @property
    @memoize
    def even_odd(self):
        """
        Selects even-odd nuclei from the table
        """
        return self.select(lambda Z, N: not (Z % 2) and (N % 2), name=self.name)

    @property
    @memoize
    def even_even(self):
        """
        Selects even-even nuclei from the table
        """
        return self.select(lambda Z, N: not (Z % 2) and not (N % 2), name=self.name)

    def error(self, relative_to: str = "AME2003") -> Table:
        """
        Calculate error difference

        Parameters:

            relative_to: a valid mass table name

        Example
        -------

            >>> Table('DUZU').error(relative_to='AME2003').dropna()
            Z    N
            8    8      0.667001
                9      0.138813
                10    -0.598478
                11    -0.684870
                12    -1.167462
        """
        df = self.df - Table(relative_to).df
        return Table(df=df)

    def rmse(self, relative_to: str = "AME2003"):
        """Calculate root mean squared error

        Parameters:

            relative_to: a valid mass table name.

        Example

            >>> template = '{0:10}|{1:^6.2f}|{2:^6.2f}|{3:^6.2f}'
            >>> print('Model      ', 'AME95 ', 'AME03 ', 'AME12 ')  #  Table header
            ... for name in Table.names:
            ...     print(template.format(name, Table(name).rmse(relative_to='AME1995'),
            ...                             Table(name).rmse(relative_to='AME2003'),
            ...                             Table(name).rmse(relative_to='AME2012')))
            Model       AME95  AME03  AME12
            AME2003   | 0.13 | 0.00 | 0.13
            AME2003all| 0.42 | 0.40 | 0.71
            AME2012   | 0.16 | 0.13 | 0.00
            AME2012all| 0.43 | 0.43 | 0.69
            AME1995   | 0.00 | 0.13 | 0.16
            AME1995all| 0.00 | 0.17 | 0.21
            DUZU      | 0.52 | 0.52 | 0.76
            FRDM95    | 0.79 | 0.78 | 0.95
            KTUY05    | 0.78 | 0.77 | 1.03
            ETFSI12   | 0.84 | 0.84 | 1.04
            HFB14     | 0.84 | 0.83 | 1.02
        """

        error = self.error(relative_to=relative_to)
        return math.sqrt((error.df ** 2).mean())

    @property
    @memoize
    def binding_energy(self):
        """
        Return binding energies instead of mass excesses
        """
        M_P = 938.2723
        # MeV
        M_E = 0.5110
        # MeV
        M_N = 939.5656
        # MeV
        AMU = 931.494028
        # MeV
        df = self.Z * (M_P + M_E) + (self.A - self.Z) * M_N - (self.df + self.A * AMU)
        return Table(df=df, name="BE" + "(" + self.name + ")")

    @property
    @memoize
    def q_alpha(self):
        """Return Q_alpha"""

        M_ALPHA = 2.4249156  # He4 mass excess in MeV
        f = lambda parent, daugther: parent - daugther - M_ALPHA
        return self.derived("Q_alpha", (-2, -2), f)

    @property
    @memoize
    def q_beta(self):
        """Return Q_beta"""

        f = lambda parent, daugther: parent - daugther
        return self.derived("Q_beta", (1, -1), f)

    @property
    @memoize
    def s2n(self):
        """Return 2 neutron separation energy"""

        M_N = 8.0713171  # neutron mass excess in MeV
        f = lambda parent, daugther: -parent + daugther + 2 * M_N
        return self.derived("s2n", (0, -2), f)

    @property
    @memoize
    def s1n(self) -> Table:
        """Return 1 neutron separation energy"""

        M_N = 8.0713171  # neutron mass excess in MeV
        f = lambda parent, daugther: -parent + daugther + M_N
        return self.derived("s1n", (0, -1), f)

    @property
    @memoize
    def s2p(self):
        """Return 2 proton separation energy"""

        M_P = 7.28897050  # proton mass excess in MeV
        f = lambda parent, daugther: -parent + daugther + 2 * M_P
        return self.derived("s2p", (-2, 0), f)

    @property
    @memoize
    def s1p(self):
        """Return 1 proton separation energy"""

        M_P = 7.28897050  # proton mass excess in MeV
        f = lambda parent, daugther: -parent + daugther + M_P
        return self.derived("s1p", (-1, 0), f)

    def derived(self, name: str, relative_coords: Tuple[int, int], formula: Callable):
        """Helper function for derived quantities"""

        dZ, dN = relative_coords
        daughter_idx = [(Z + dZ, N + dN) for Z, N in self.df.index]
        idx = self.df.index.intersection(daughter_idx)
        values = formula(self.df.values, self.df.reindex(daughter_idx).values)
        return Table(
            df=pd.Series(values, index=self.df.index, name=name + "(" + self.name + ")")
        )

    @property
    @memoize
    def ds2n(self):
        """Calculates the derivative of the neutron separation energies:

        ds2n(Z,A) = s2n(Z,A) - s2n(Z,A+2)
        """

        idx = [(x[0] + 0, x[1] + 2) for x in self.df.index]
        values = self.s2n.values - self.s2n.loc[idx].values
        return Table(
            df=pd.Series(
                values, index=self.df.index, name="ds2n" + "(" + self.name + ")"
            )
        )

    @property
    @memoize
    def ds2p(self):
        """Calculates the derivative of the neutron separation energies:

        ds2n(Z,A) = s2n(Z,A) - s2n(Z,A+2)
        """

        idx = [(x[0] + 2, x[1]) for x in self.df.index]
        values = self.s2p.values - self.s2p.loc[idx].values
        return Table(
            df=pd.Series(
                values, index=self.df.index, name="ds2p" + "(" + self.name + ")"
            )
        )

    def __repr__(self):
        return self.df.__repr__()

    def __str__(self):
        return self.df.__str__()

    def join(self, join="outer", *tables):
        return Table(df=pd.concat([self.df] + [table.df for table in tables], axis=1))

    def chart_plot(
        self,
        ax=None,
        cmap: str = "RdBu",
        xlabel: str = "N",
        ylabel: str = "Z",
        grid_on: bool = True,
        colorbar: bool = True,
        save_path: str = None,
    ):
        """Plot a nuclear chart with (N,Z) as axis and the values
        of the Table as a color scale

        Parameters:

            ax: optional matplotlib axes
                    defaults to current axes
            cmap: a matplotlib colormap
                    default: 'RdBu'
            xlabel: string representing the label of the x axis
                default: 'N'
            ylabel: string, default: 'Z'
                the label of the x axis
            grid_on: (boolean), default: True,
                whether to draw the axes grid or not
            colorbar: boolean, default: True
                whether to draw a colorbar or not

        Returns:

            ax: a matplotlib axes object

        Example
        -------
        Plot the theoretical deviation for the Möller's model::

            >>> Table('FRDM95').error().chart_plot()

        """
        from scipy.interpolate import griddata
        from numpy import linspace, meshgrid
        import matplotlib.pyplot as plt

        # extract the 1D arrays to be plotted
        x = self.dropna().N
        y = self.dropna().Z
        z = self.dropna().values

        # convert to matplotlibs grid format
        xi = linspace(min(x), max(x), max(x) - min(x) + 1)
        yi = linspace(min(y), max(y), max(y) - min(y) + 1)
        X, Y = meshgrid(xi, yi)

        Z = griddata((x, y), z, (X, Y), method="linear")

        # create and customize plot
        if ax is None:
            ax = plt.gca()
        chart = ax.pcolormesh(X, Y, Z, cmap=cmap, shading="auto")
        ax.set_xlabel(xlabel)
        ax.set_ylabel(ylabel)
        ax.grid(grid_on)
        ax.set_aspect("equal")
        if colorbar:
            plt.colorbar(chart)
        if save_path is not None:
            fig = plt.gcf()
            fig.savefig(save_path)
        return ax

    def chart_altair(
        self,
        title: str = "",
        width: int = 600,
        path: str = None,
        scheme="viridis",
        fmt=".2f",
        overlay_text: bool = True,
        legend_orientation="vertical",
    ):
        import altair as alt

        data = self.df.dropna().reset_index()[["Z", "N"]]
        data["color"] = self.df.dropna().values

        base = alt.Chart(data).encode(
            alt.X("N:O", scale=alt.Scale(paddingInner=0)),
            alt.Y(
                "Z:O",
                scale=alt.Scale(paddingInner=0),
                sort=alt.EncodingSortField("Z", order="descending"),
            ),
        )

        chart = base.mark_rect().encode(
            color=alt.Color(
                "color:Q",
                scale=alt.Scale(scheme=scheme),
                legend=alt.Legend(direction=legend_orientation),
                title=title,
            )
        )

        if overlay_text:
            text = base.mark_text(baseline="middle").encode(
                text=alt.Text("color:Q", format=fmt)
            )
            chart = chart + text

        x_range = data["N"].max() - data["N"].min()
        y_range = data["Z"].max() - data["Z"].min()

        height = round(width * y_range / x_range)
        chart = chart.properties(width=width, height=height)

        if path is not None:
            chart.save(path)
        return chart
