
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

let table = new DataTable('#devices',
{
    columns:
    [
        { title: 'Назва та тип РЕЗ або ВП, найменування виробника' },
        { title: 'Радіотехнології' },
        { title: 'Призначення' },
        { title: 'Смуги радіочастот, МГц' }
    ],
    data: devices,
    layout:
    {
        topEnd: function ()
        {
            let toolbar = document.createElement('div');
            toolbar.innerHTML =
                `Частота, МГц: <input type="search" id="FrequencyInput" />
                &emsp;Текст: <input type="search" id="TextInput" />`;
            return toolbar;
        },
    },
    order: []
});

let frequencySearchValue = NaN
let textSearchValue = ''

function Search(string, device, _)
{
    if (!Number.isNaN(frequencySearchValue))
    {
        let found = false

        for (let frequency of device[columns.frequencies])
        {
            if (frequency.length == 1)
            {
                if (frequency[0] == frequencySearchValue)
                {
                    found = true;
                    break;
                }
            }
            else
            {
                if (frequencySearchValue >= frequency[0] && frequencySearchValue <= frequency[1])
                {
                    found = true;
                    break;
                }
            }
        }

        if (!found)
            return false;
    }

    if (textSearchValue != '')
    {
        return string.toLowerCase().includes(textSearchValue);
    }

    return true;
}

$('#FrequencyInput').on('keyup', function()
{
    let value = FrequencyInput.value;
    frequencySearchValue = value == '' ? NaN : Number(value);
    table.search(Search).draw();
});

$('#TextInput').on('keyup', function()
{
    textSearchValue = TextInput.value.toLowerCase();
    table.search(Search).draw();
});
