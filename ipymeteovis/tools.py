class Colors:
    def __init__(self):
        pass

    def jet(self, v_min, v_max):
        """
        Create jet colormap based on the input min and max value.
        Out-of-boarder values will be assigned to fully transparent.

        There are four levels of scale, checking following this order:
        - [0, 1]
        - [0, 10]
        - [-50, 100]
        - others => [-50, 350]

        :param v_min:
        :param v_max:
        :return:
        """
        print(v_min, v_max)
