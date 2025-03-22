
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

let spectrumToolbar = document.createElement('div');

let table = new DataTable('#devices',
{
    columns:
    [
        { title: 'Назва та тип РЕЗ або ВП, найменування виробника', width: '50%' },
        { title: 'Радіотехнології', width: '20%' },
        { title: 'Призначення', width: '20%' },
        { title: 'Смуги радіочастот, МГц' }
    ],
    data: devices,
    layout:
    {
        topStart: null,
        topEnd: null,
        top: spectrumToolbar,
        top2Start: 'pageLength',
        top2End: function ()
        {
            let toolbar = document.createElement('div');
            toolbar.innerHTML =
                `Частота, МГц: <input type="search" id="FrequencyInput" />
                &emsp;Текст: <input type="search" id="TextInput" />`;
            return toolbar;
        },
    },
    language:
    {
        "info": "Показано від _START_ по _END_ з _TOTAL_ пристроїв",
        "infoEmpty": "Показано 0 пристроїв",
        "infoFiltered": "(відфільтровано з _MAX_ пристроїв)",
        "lengthMenu": "Пристроїв на сторінці: _MENU_",
        "paginate":
        {
            "first": "Перша",
            "previous": "Попередня",
            "next": "Наступна",
            "last": "Остання"
        },
        "thousands": "",
        "zeroRecords": "Не знайдено жодного пристрою",
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

    if (textSearchValue)
        return string.toLowerCase().includes(textSearchValue);

    return true;
}

$('#FrequencyInput').on('keyup', function()
{
    let value = FrequencyInput.value;
    let frequency = value ? Number(value) : NaN;
    let bands = Array();

    if (!Number.isNaN(frequency))
    {
        for (let band of spectrum)
        {
            if (frequency >= band[0] && frequency <= band[1])
                bands.push(band)
        }
    }

    let bandsTable = '';

    if (bands.length > 0)
    {
        bandsTable = '<table id="spectrum">';

        for (let band of bands)
            bandsTable += `<tr><td>${band[0]}&nbsp;&#8288;-&#8288;&nbsp;${band[1]}</td><td>${band[2]}</td><td>${band[3]}</td><td>${band[4]}</td></tr>`;

        bandsTable += '</table>';
    }

    frequencySearchValue = frequency;
    spectrumToolbar.innerHTML = bandsTable;
    table.search(Search).draw();
});

$('#TextInput').on('keyup', function()
{
    textSearchValue = TextInput.value.toLowerCase();
    table.search(Search).draw();
});
