# Asiamiestutkinto-trainer

Epävirallinen, avoimiin vastaus- ja esseetehtäviin keskittyvä harjoittelusovellus Suomen auktorisoidun teollisoikeusasiamiehen tutkintoon. Sovellus näyttää vanhan aidon koekysymyksen ja pyytää OpenAI-mallilta arvioinnin vain kyseisen koevuoden virallisen mallivastauksen/arvosteluperusteiden pohjalta.

> **Huomaa:** arviointi on tekoälyavusteinen harjoitusarvio eikä takaa virallisen arvostelijan antamaa pistemäärää. Historiallinen aineisto ei kuvaa välttämättä nykyistä oikeustilaa. Tarkista ajantasainen lainsäädäntö, määräykset, ohjeet ja oikeuskäytäntö erikseen.

## Google Colab (suositeltu)

1. Avaa `Trainer.ipynb` GitHubista Colabissa.
2. Suorita solut järjestyksessä. Ensimmäinen asentaa riippuvuudet ja tarvittaessa kloonaa repositorion.
3. Syötä API-avain piilotettuun kyselyyn. Avain asetetaan vain istunnon ympäristömuuttujaan eikä sitä tallenneta notebookiin tai historiaan.
4. Käyttöliittymä käynnistyy ilman koodin muokkaamista. Valitse osa, vuosi, kategoria ja tehtävä tai arvo tehtävä.

Arvosteluaineisto pysyy piilossa ennen arviointia. Arvioinnin jälkeen sen voi näyttää erillisellä painikkeella. Istuntohistorian voi ladata JSON- tai CSV-tiedostona. Mallin voi vaihtaa asettamalla `GPT_MODEL`-ympäristömuuttujan (oletus `gpt-4o-mini`).

## Paikallinen asennus ja komentorivi

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export OPENAI_API_KEY='...'
python app.py --list
python app.py --id common-2020-ethics-a < vastaus.txt
python app.py --random --answer-file vastaus.txt
```

CLI ja Colab käyttävät samaa `trainer`-paketin datalatausta, validointia ja arviointimoottoria. API-avainta ei saa lisätä tiedostoihin tai versionhallintaan.

## Arvioinnin periaatteet

- Pisteytys perustuu yksinomaan tehtävään tallennettuun koevuoden viralliseen aineistoon; sovellus ei tee oikeudellista verkkotutkimusta.
- `explicit_structured` pisteytetään virallisin kriteerein, `official_text_with_explicit_points` noudattaa tekstin nimenomaisia pisteitä ja `official_text_holistic` arvioidaan kokonaisuutena ilman keksittyä osapistejakoa.
- Python tarkistaa pistealueen ja kriteerit sekä laskee 50 %:n harjoittelurajan ja hyväksymistuloksen. Moniosaisen virallisen ryhmän tulosta ei väitetä hyväksytyksi ennen kaikkien osien arviointia.
- Historiallista oikeustilaa koskeva aineiston huomautus näytetään jokaisen arvion lopussa.

## Rakenne

- `trainer/data.py`: ainoan auktoritatiivisen kysymyslähteen lataus ja suodatus
- `trainer/grader.py`: arviointikehote, OpenAI-rajapinta ja deterministinen validointi
- `trainer/models.py`: sovelluksen tietomallit ja ennen vastausta turvallinen näkymä
- `trainer/ui_colab.py`: Colab/Jupyter-käyttöliittymä
- `trainer/history.py`: istuntohistoria ja JSON/CSV-vienti
- `exam_data/data/items.jsonl`: **ainoa ajonaikainen arvioitavien tehtävien lähde**
- `exam_data/data/ungraded_items.json`: tarkoituksella automaattiarvioinnin ulkopuolelle jätetyt tehtävät
- `exam_data/data/pending_sources.json`: keskeneräiset lähteet, ei harjoitustehtäviä
- `exam_data/schema`, `exam_data/sources`: skeema ja säilytetty lähde/provenienssitieto

## Aineiston validointi ja testit

Samat tarkistukset suoritetaan automaattisesti GitHub Actionsissa jokaiselle pull requestille ja `main`-haaraan vietävälle muutokselle. Paikallisesti ne voi suorittaa näin:

```bash
python exam_data/scripts/validate_data.py
pytest
python -m compileall trainer app.py
```

## Uuden koekysymyksen lisääminen

1. Lisää viralliseen lähteeseen täsmällisesti perustuva tietue `exam_data/data/items.jsonl`-tiedostoon ja vastaava vuosikohtainen aineisto. Älä muotoile juridista sisältöä uudelleen.
2. Säilytä lähteen tiedosto-, rivi- ja provenienssitiedot. Valitse arvostelutila aineiston todellisen tarkkuuden perusteella; älä keksi enimmäispisteitä, kriteerejä tai pistejakoa.
3. Jos luotettavaa enimmäispistemäärää tai arvosteluperustetta ei ole, lisää aineisto `ungraded_items.json`- tai `pending_sources.json`-tiedostoon, ei ajonaikaiseen kysymyspankkiin.
4. Päivitä vuosikohtainen JSON ja `exam_data/INDEX.md`, suorita validaattori ja testit ja lisää tarvittavat testit.

Aineiston yksityiskohtaiset säännöt ovat tiedostoissa `exam_data/grading_policy.md` ja `exam_data/README.md`.
