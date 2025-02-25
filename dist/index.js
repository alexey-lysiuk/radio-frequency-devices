
for (let device of devices)
{
    for (let frequency of device[1])
    {
        frequency.toString = function ()
        {
            return this.length > 1 ? `${this[0]}&nbsp;&#8288;-&#8288;&nbsp;${this[1]}` : this[0];
        }
    }

    device[1].toString = function ()
    {
        return this.join('<br>');
    }
}

new DataTable('#devices',
{
    columns:
    [
        { title: 'Name' },
        { title: 'Range' }
    ],
    data: devices,
});
