from datetime import date
from freezegun import freeze_time
from onegov.agency.collections import ExtendedAgencyCollection
from onegov.agency.collections import ExtendedPersonCollection
from onegov.agency.pdf import AgencyPdfAr
from onegov.agency.pdf import AgencyPdfDefault
from onegov.agency.pdf import AgencyPdfZg
from PyPDF2 import PdfFileReader


def test_pdf_page_break_on_level(session):
    pass


def test_agency_pdf_default(session):
    people = ExtendedPersonCollection(session)
    aeschi = people.add(
        last_name="Aeschi",
        first_name="Thomas",
        political_party="SVP"
    )
    eder = people.add(
        last_name="Eder",
        first_name="Joachim",
        political_party="FDP"
    )

    agencies = ExtendedAgencyCollection(session)
    bund = agencies.add_root(title="Bundesbehörden")
    canton = agencies.add_root(title="Kanton")
    nr = agencies.add(
        parent=bund,
        title="Nationalrat",
        portrait="Portrait NR",
        export_fields=[
            'membership.title',
            'person.title'
        ]
    )
    sr = agencies.add(
        parent=bund,
        title="Ständerat",
        export_fields=[
            'person.first_name',
            'person.last_name',
            'person.political_party',
        ]
    )

    nr.add_person(aeschi.id, "Mitglied von Zug")
    sr.add_person(eder.id, "Ständerat für Zug")

    # test single agency with toc break on level 1
    file = AgencyPdfDefault.from_agencies(
        agencies=[bund],
        title="Staatskalender",
        toc=True,
        exclude=[],
        page_break_on_level=1
    )
    reader = PdfFileReader(file)
    assert reader.getNumPages() == 2, 'No page break since its on level 1'
    page1_toc = reader.getPage(0).extractText()
    page2 = reader.getPage(1).extractText()

    assert "Staatskalender" in page1_toc
    assert "1 Bundesbehörden" in page1_toc
    assert "1.1 Nationalrat" in page1_toc
    assert "1.2 Ständerat" in page1_toc
    assert "1 Bundesbehörden" in page2
    assert "1.1 Nationalrat" in page2
    assert "Portrait NR" in page2
    assert "Mitglied von Zug" in page2
    assert "Aeschi Thomas" in page2
    assert "SVP" not in page2
    assert "1.2 Ständerat" in page2
    assert "Ständerat für Zug" not in page2
    assert "Joachim, Eder, FDP" in page2

    # test page break on level 2
    file = AgencyPdfDefault.from_agencies(
        agencies=[bund],
        title="Staatskalender",
        toc=True,
        exclude=[],
        page_break_on_level=2
    )
    reader = PdfFileReader(file)
    assert reader.getNumPages() == 3, 'No page break since its on level 1'
    page3 = reader.getPage(2).extractText()
    assert "1.2 Ständerat" in page3
    assert "Ständerat für Zug" not in page3
    assert "Joachim, Eder, FDP" in page3

    # test page break on level 1 with succeeding headers
    file = AgencyPdfDefault.from_agencies(
        agencies=[bund, canton],
        title="Staatskalender",
        toc=True,
        exclude=[],
        page_break_on_level=1
    )
    reader = PdfFileReader(file)
    assert reader.getNumPages() == 3, 'Page break since its on level 1'
    assert "2 Kanton" in reader.getPage(2).extractText()
    assert "2 Kanton" in reader.getPage(0).extractText()

    file = AgencyPdfDefault.from_agencies(
        agencies=[nr, sr],
        title="Staatskalender",
        toc=False,
        exclude=['political_party']
    )
    reader = PdfFileReader(file)
    pdf = '\n'.join([
        reader.getPage(page).extractText()
        for page in range(reader.getNumPages())
    ])
    assert "Staatskalender" in pdf
    assert "Bundesbehörden" not in pdf
    assert "FDP" not in pdf
    assert "SVP" not in pdf

    file = AgencyPdfDefault.from_agencies(
        agencies=[nr],
        title="Nationalrat",
        toc=False,
        exclude=[]
    )
    reader = PdfFileReader(file)
    pdf = '\n'.join([
        reader.getPage(page).extractText()
        for page in range(reader.getNumPages())
    ])
    assert reader.getNumPages() == 1
    assert pdf == (
        '1\nNationalrat\nPortrait NR\nMitglied von Zug\nAeschi Thomas\n'
    )


def test_agency_pdf_default_hidden(session):
    people = ExtendedPersonCollection(session)
    aeschi = people.add(
        last_name="Aeschi",
        first_name="Thomas",
        is_hidden_from_public=True
    )
    eder = people.add(
        last_name="Eder",
        first_name="Joachim"
    )

    agencies = ExtendedAgencyCollection(session)
    bund = agencies.add_root(title="Bundesbehörden")
    agencies.add(
        parent=bund,
        title="Bundesrat",
        is_hidden_from_public=True
    )
    nr = agencies.add(
        parent=bund,
        title="Nationalrat",
        export_fields=['membership.title', 'person.title']
    )
    sr = agencies.add(
        parent=bund,
        title="Ständerat",
        export_fields=['membership.title', 'person.title']
    )

    nr.add_person(aeschi.id, "Mitglied von Zug")
    sr.add_person(eder.id, "Ständerat für Zug", is_hidden_from_public=True)

    file = AgencyPdfDefault.from_agencies(
        agencies=[bund],
        title="Staatskalender",
        toc=False,
        exclude=[]
    )
    reader = PdfFileReader(file)
    pdf = '\n'.join([
        reader.getPage(page).extractText()
        for page in range(reader.getNumPages())
    ])
    assert "Bundesrat" not in pdf
    assert "Nationalrat" in pdf
    assert "Ständerat" in pdf
    assert "Mitglied von Zug" not in pdf
    assert "Aeschi" not in pdf
    assert "Ständerat für Zug" not in pdf
    assert "Eder" not in pdf


@freeze_time("2018-01-01")
def test_agency_pdf_ar(session):
    people = ExtendedPersonCollection(session)
    aeschi = people.add(
        last_name="Aeschi",
        first_name="Thomas",
        political_party="SVP"
    )
    eder = people.add(
        last_name="Eder",
        first_name="Joachim",
        political_party="FDP"
    )

    agencies = ExtendedAgencyCollection(session)
    bund = agencies.add_root(title="Bundesbehörden")
    nr = agencies.add(
        parent=bund,
        title="Nationalrat",
        portrait="Portrait NR",
        export_fields=[
            'membership.title',
            'person.title'
        ]
    )
    sr = agencies.add(
        parent=bund,
        title="Ständerat",
        export_fields=[
            'person.first_name',
            'person.last_name',
            'person.political_party',
        ]
    )

    nr.add_person(aeschi.id, "Mitglied von AR")
    sr.add_person(eder.id, "Ständerat für AR")

    file = AgencyPdfAr.from_agencies(
        agencies=[bund],
        title="Staatskalender",
        toc=True,
        exclude=[]
    )
    reader = PdfFileReader(file)
    assert reader.getNumPages() == 2

    page1 = reader.getPage(0).extractText()
    page2 = reader.getPage(1).extractText()
    assert page1 == (
        f'Druckdatum: {date.today():%d.%m.%Y}\n1\n'
        'Staatskalender\n2\n'
        '1 Bundesbehörden\n2\n'
        '1.1 Nationalrat\n2\n'
        '1.2 Ständerat\n'
    )
    assert page2 == (
        f'Staatskalender Kanton Appenzell Ausserrhoden\n'
        f'Druckdatum: {date.today():%d.%m.%Y}\n2\n'
        f'1 Bundesbehörden\n'
        f'1.1 Nationalrat\n'
        f'Portrait NR\n'
        f'Mitglied von AR\nAeschi Thomas\n'
        f'1.2 Ständerat\n'
        f'Joachim, Eder, FDP\n'
    )


def test_agency_pdf_zg(session):
    people = ExtendedPersonCollection(session)
    aeschi = people.add(
        last_name="Aeschi",
        first_name="Thomas",
        political_party="SVP"
    )
    eder = people.add(
        last_name="Eder",
        first_name="Joachim",
        political_party="FDP"
    )

    agencies = ExtendedAgencyCollection(session)
    bund = agencies.add_root(title="Bundesbehörden")
    nr = agencies.add(
        parent=bund,
        title="Nationalrat",
        portrait="Portrait NR",
        export_fields=[
            'membership.title',
            'person.title'
        ]
    )
    sr = agencies.add(
        parent=bund,
        title="Ständerat",
        export_fields=[
            'person.first_name',
            'person.last_name',
            'person.political_party',
        ]
    )

    nr.add_person(aeschi.id, "Mitglied von Zug")
    sr.add_person(eder.id, "Ständerat für Zug")

    file = AgencyPdfZg.from_agencies(
        agencies=[bund],
        title="Staatskalender",
        toc=True,
        exclude=[]
    )
    reader = PdfFileReader(file)
    pdf = '\n'.join([
        reader.getPage(page).extractText()
        for page in range(reader.getNumPages())
    ])

    assert pdf == (
        f'Staatskalender\n2\n'
        f'1 Bundesbehörden\n2\n'
        f'1.1 Nationalrat\n2\n'
        f'1.2 Ständerat\n\n'
        f'Staatskalender\n'
        f'Druckdatum: {date.today():%d.%m.%Y}\n2\n'
        f'1 Bundesbehörden\n'
        f'1.1 Nationalrat\n'
        f'Portrait NR\n'
        f'Mitglied von Zug\n'
        f'Aeschi Thomas\n'
        f'1.2 Ständerat\n'
        f'Joachim, Eder, FDP\n'
    )
