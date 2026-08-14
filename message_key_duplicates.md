# Message key duplicates — candidates for unification

After the cleanup: **1505 keys** (was 1708). 203 unused removed, 2 uncategorised keys prefixed.

## A. Same English, same Russian and Tajik — mechanical merge (31 groups)

Nothing is lost by collapsing these to one key.

| Suggested key | Duplicates | English |
|---|---|---|
| `mdrtb.pv.total` | `mdrtb.form8.total`, `mdrtb.tb07u.total`, `mdrtb.tb08u.total`, `mdrtb.tb08u.totalRow` | Total |
| `mdrtb.age` | `mdrtb.ageUpper`, `mdrtb.form89.ageAtRegistration`, `mdrtb.tb03.age` | Age |
| `mdrtb.tb03.patientGroup` | `mdrtb.tb03.registrationGroup`, `mdrtb.tb07u.registrationGroup`, `mdrtb.tb08u.registrationGroup` | Registration Group |
| `general.instructions` | `labtest.instructions`, `mdrtb.instructions` | Instructions |
| `mdrtb.comments` | `mdrtb.pv.comments`, `mdrtb.pv.register.comments` | Comments |
| `mdrtb.year` | `mdrtb.pv.year`, `mdrtb.viewClosedReports.year` | Year |
| `general.specimenSite` | `labtest.specimenSite` | Specimen Site |
| `general.specimenType` | `labtest.specimenType` | Specimen Type |
| `mdrtb.female` | `mdrtb.gender.F` | Female |
| `mdrtb.followupForm` | `mdrtb.followUpVisits` | Form89 |
| `mdrtb.form8.includingInPHC` | `mdrtb.form8.includingPHCDiagnosed` | Including in PHC |
| `mdrtb.form89.ptbSite` | `mdrtb.form89.eptbLocation` | Clinical Diagnosis |
| `mdrtb.male` | `mdrtb.gender.M` | Male |
| `mdrtb.hain` | `mdrtb.hain1` | HAIN1 |
| `mdrtb.hain2` | `mdrtb.tb03.hain2` | HAIN2 |
| `mdrtb.hainFormatter` | `mdrtb.hain2Formatter` | {0}/{1}/{2} on {3}, tested at {4} |
| `mdrtb.inhResult` | `mdrtb.inhResistance` | INH Resistance |
| `mdrtb.outcome` | `mdrtb.lists.outcome` | Outcome |
| `mdrtb.oblast` | `mdrtb.viewClosedReports.oblast` | Oblast |
| `mdrtb.rifResult` | `mdrtb.rifResistance` | RIF Resistance |
| `mdrtb.sldreport.and` | `mdrtb.specimenReports.dateRange2` | and |
| `mdrtb.startdate` | `mdrtb.sldreport.startDate` | Start Date |
| `mdrtb.tb03.cured` | `mdrtb.tb08u.cured` | Cured |
| `mdrtb.tb03.failure` | `mdrtb.tb08u.failure` | Treatment<br/>Failure |
| `mdrtb.tb03.txCompleted` | `mdrtb.tb08u.txCompleted` | Treatment<br/>Completed |
| `mdrtb.tb07u.afterDefault` | `mdrtb.tb08u.afterDefault` | Default after treatment <br/>on regimen |
| `mdrtb.tb07u.afterFailure` | `mdrtb.tb08u.afterFailure` | Failure after treatment <br/>on regimen |
| `mdrtb.tb07u.regionCityDistrict` | `mdrtb.tb08u.regionCityDistrict` | Region/City/District: |
| `mdrtb.tb07u.relapse` | `mdrtb.tb08u.relapse` | Relapse after treatment<br/>on regimen</td> |
| `mdrtb.tb07u.signature` | `mdrtb.tb08u.signature` | Signature: |
| `User.username` | `options.login.username` | Username |

## B. Same English, but the Russian differs — needs your call (85 groups)

These are *not* safe to merge blindly: the English collided but a translator
distinguished them in Russian, so one of the two Russian strings would be lost.

| Keys | English | Russian variants |
|---|---|---|
| `labtest.testgroup.other`, `mdrtb.form89.otherDisease`, `mdrtb.pv.other`, `mdrtb.pv.otherDrug2Dose`, `mdrtb.sldreport.other`, `mdrtb.tb03.other`, `mdrtb.tb07u.other`, `mdrtb.tb08u.other` | other | ДРУГОЕ / Другой |
| `mdrtb.cultureResult`, `mdrtb.result`, `mdrtb.smearResult`, `mdrtb.tb03.result` | result | Результат |
| `mdrtb.date`, `mdrtb.datelowercase`, `mdrtb.tb03.date`, `mdrtb.tb03u.dateOfResistanceTypeDuringTreatment` | date | Дата / дата |
| `mdrtb.district`, `mdrtb.enrolledLocation`, `mdrtb.sldreport.district`, `mdrtb.viewClosedReports.district` | district | Округ / Район / Район - Регион |
| `mdrtb.addTransferInVisit`, `mdrtb.lists.transferIn`, `mdrtb.transferIn` | transfer in | Перевод в / Перенос / Трансфер в |
| `general.cancel`, `mdrtb.cancel`, `mdrtb.cancellowercase` | cancel | Отмена |
| `Program.dateCompleted`, `mdrtb.completionDate`, `mdrtb.enrollment.completionDate` | completion date | Дата выполнения / Дата завершения |
| `mdrtb.dq.dob`, `mdrtb.pv.register.patientBirthdate`, `mdrtb.tb03.dateOfBirth` | date of birth | Дата рождения |
| `Person.gender`, `mdrtb.dq.gender`, `mdrtb.gender` | gender | Пол |
| `general.new`, `mdrtb.form8.fromNew`, `mdrtb.new` | new | Новые функции / Новый |
| `Program.location`, `mdrtb.identifierLocation`, `mdrtb.location` | location | Локация / Место регистрации / Расположение |
| `mdrtb.list`, `mdrtb.listPatients`, `mdrtb.outputToList` | list | Перечень / Список |
| `mdrtb.lists.new`, `mdrtb.tb07u.newCases`, `mdrtb.tb08u.newCases` | new cases | Новые случаи / Новый случай |
| `mdrtb.mdrtb`, `mdrtb.title`, `mdrtb.title.homepage` | mdr-tb | Главная страница ТБ / МЛУ ТБ / Регистр ТБ (OpenMRS) для Таджикистана |
| `mdrtb.month`, `mdrtb.tb03.month`, `mdrtb.viewClosedReports.month` | month | Месяц / мес. |
| `mdrtb.pv.quarter`, `mdrtb.quarter`, `mdrtb.viewClosedReports.quarter` | quarter | Квартал / Четверть |
| `mdrtb.pv.reportDate`, `mdrtb.tb07u.dateOfReport`, `mdrtb.tb08u.dateOfReport` | date of report | Дата отчета / Дата отчета: |
| `mdrtb.tb07u.eptb`, `mdrtb.tb08.eptb`, `mdrtb.tb08u.eptb` | ep-tb | EP-TB / ЭП-ТБ |
| `general.view`, `mdrtb.view`, `mdrtb.viewClosedReports.viewBtn` | view | Вид / Просмотреть |
| `general.careSetting`, `labtest.careSetting` | care setting | Настройка ухода / Условия оказания помощи |
| `ConceptProposal.encounter`, `general.encounter` | encounter | Взаимодействия с пациентом / Визит |
| `general.labTestType`, `labtest.labTestType` | lab test type | Тип анализа / Тип лабораторного исследования |
| `general.name`, `mdrtb.name` | name | Имя / Название |
| `general.referenceConcept`, `labtest.referenceConcept` | reference concept | Связанная концепция / Ссылочное понятие |
| `general.status`, `labtest.status` | status | Статус |
| `general.test.retire`, `labtest.labtesttype.void` | retire test type | Вывести тип исследования из использования / Удалить тип анализа |
| `general.testGroup`, `labtest.testGroup` | test group | Группа анализов / Группа исследований |
| `general.testType`, `labtest.testType` | test type | Тип анализа / Тип исследования |
| `general.add`, `mdrtb.add` | add | Добавить |
| `Location.address1`, `mdrtb.address` | address | Адрес |
| `Location.address2`, `mdrtb.address2` | address 2 | Адрес 2 |
| `mdrtb.addTransferOutVisit`, `mdrtb.transferOut` | transfer out | Перевод из / Трансфер из |
| `Person.birthdate`, `mdrtb.birthdate` | birthdate | Дата рождения / День рождения |
| `Location.cityVillage`, `mdrtb.cityvillage` | city/village | Город/Деревня / Город/Село |
| `general.close`, `mdrtb.close` | close | Закрыть |
| `mdrtb.cultureFormatter`, `mdrtb.smearFormatter` | {0} on {1}, tested at {2} | {0} на (дата) {1}, анализ проведен (время) {2} / {0} на {1}, исследовано в {2} |
| `general.delete`, `mdrtb.delete` | delete | Удалить |
| `DrugOrder.dose`, `mdrtb.dose` | dose | Доза / Дозировка |
| `mdrtb.dotsreport07`, `mdrtb.tb07` | tb-07 | TB-07у / ТБ 07 |
| `mdrtb.dq.fullName`, `mdrtb.tb03.fullName` | full name | ФИО |

_45 further groups omitted._
