
const columns =
{
    frequencies: 3,
}

for (let device of devices)
{
    for (let frequency of device[columns.frequencies])
    {
        frequency.toString = function ()
        {
            return this.length > 1 ? `${this[0]}&nbsp;&#8288;-&#8288;&nbsp;${this[1]}` : this[0];
        }
    }

    device[columns.frequencies].toString = function ()
    {
        return this.join('<br>');
    }
}

new DataTable('#devices',
{
    columns:
    [
        { title: 'Назва та тип РЕЗ або ВП, найменування виробника' },
        { title: 'Радіотехнології' },
        { title: 'Призначення' },
        { title: 'Смуги радіочастот' }
    ],
    data: devices,
    order: []
});
