# draft test for plotting._add_component
def test_add_component():
    """add components with all 8 possible anchors"""
    fig, ax = plt.subplots(1,1)

    ax.set(
        aspect='equal',
        xlim=(-2.5,2.5),
        ylim=(-2,2)
    )
    ax.grid(True)

    add_component(ax, (1,1), anchor='SW', width=1, height=2/3,
                  label='Comp A\n1 MW', color='b')
    add_component(ax, (1,0), anchor='W', width=1, height=2/3,
                  label='Comp B\n1 MW', color='r')
    add_component(ax, (1,-1), anchor='NW', width=1, height=2/3, color='g')

    add_component(ax, (-1,1), anchor='SE', width=1, height=2/3, color='b')
    add_component(ax, (-1,0), anchor='E', width=1, height=2/3, color='r')
    add_component(ax, (-1,-1), anchor='NE', width=1, height=2/3, color='g')

    add_component(ax, (0,1), anchor='S', width=1, height=2/3, color='yellow')
    add_component(ax, (0,-1), anchor='N', width=1, height=2/3, color='pink')

    ax.add_patch(Circle((0,0), radius=0.1, color='k'));