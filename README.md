# تطبيق التقييم — Evaluation

> **استطلاع العدو: ترتيب المعركة، الأنشطة اليومية، الأهداف، والموقف**
> تطبيق متكامل مبني على **Frappe Framework v16**

[![Frappe](https://img.shields.io/badge/Frappe-v16.55-blue)]()
[![Python](https://img.shields.io/badge/Python-3.14-blue)]()
[![Node](https://img.shields.io/badge/Node-24-green)]()
[![License](https://img.shields.io/badge/License-MIT-yellow)]()

---

## فهرس المحتويات

1. [نظرة عامة](#نظرة-عامة)
2. [المتطلبات](#المتطلبات)
3. [التثبيت السريع](#التثبيت-السريع)
4. [بنية التطبيق](#بنية-التطبيق)
5. [الوحدات الست](#الوحدات-الست)
6. [الوحدات الفنية (DocTypes)](#الوحدات-الفنية-doctypes)
7. [منطق العمل](#منطق-العمل)
8. [الأمان والصلاحيات](#الأمان-والصلاحيات)
9. [سير العمل (Workflows)](#سير-العمل-workflows)
10. [التقارير واللوحات](#التقارير-واللوحات)
11. [واجهة برمجة التطبيقات](#واجهة-برمجة-التطبيقات)
12. [المهام المجدولة](#المهام-المجدولة)
13. [التطوير](#التطوير)
14. [الاختبارات](#الاختبارات)

---

## نظرة عامة

التطبيق يحوّل الرصد الميداني الخام إلى صورة عملياتية متكاملة:

```
الرصد الميداني (Daily Activities)
        │
        ├──► تقرير استخباري (Intel Report)  ──► هدف (Target) ──► أمر عمليات (Operation Order)
        │
        ├──► تحديث تشكيل القوات (Force Arrangement)
        │         │
        │         ├── الجاهزية (Readiness Lines)
        │         ├── الإمداد (Logistics Lines)
        │         ├── الذخيرة (Ammunition Lines)
        │         └── مؤشر القوة القتالية (Combat Power Index)
        │
        └──► لقطة الموقف (Situation Report) ──► تقييم التهديد (Threat Assessment)
                    │
                    └──► بطاقة تقييم (Evaluation Score Card) ──► ترتيب الوحدات
```

### ما الذي يقدّمه التطبيق؟

| القدرة | الوصف |
| --- | --- |
| **رصد ميداني منظّم** | كل نشاط يومي مع الجهة، المراقب، الوحدة المرصودة، الجغرافيا، والجاهزية |
| **ترتيب معركة حيّ** | شجرة وحدات العدو مع الوضع القتالي والقوة ومؤشر القوة القتالية |
| **تقييم الوحدات** | معايير مرجّحة (أرقام، نسب، منطقي، معادلات) وبطاقات تقييم مع ترتيب تلقائي |
| **دورة الاستهداف** | من الرصد ← الاستخبارات ← الهدف ← تحليل CARVER ← تقييم الأضرار (BDA) |
| **العمليات** | أوامر العمليات، المراحل، المهام، إسناد القوات، وربط الأهداف |
| **الموقف والتهديد** | تقارير الموقف، لقطات الحالة، تقييم التهديد بقدرة×نية×فرصة |
| **الحوكمة** | صلاحيات على مستوى الوحدة، تصنيف أمني، سير عمل بموافقات، سجل تغييرات كامل |
| **التحليل** | 17 تقرير جاهز + 11 رسم بياني + 19 بطاقة رقم + 4 لوحات معلومات |

---

## المتطلبات

| المكوّن | الإصدار |
| --- | --- |
| Frappe Framework | **v16** (تم التحقق على 16.55.2) |
| Python | **3.14** (`>=3.14,<3.15`) |
| Node.js | **24** |
| MariaDB | 11.x |
| Redis | 7.x أو أحدث |
| bench | 5.x |

---

## التثبيت السريع

### 1. إعداد بيئة Frappe v16

```bash
# تثبيت bench
pip install --upgrade frappe-bench

# إنشاء bench مع إصدار 16
bench init frappe-bench --frappe-branch version-16
cd frappe-bench
```

### 2. جلب التطبيق

```bash
# من GitHub
bench get-app https://github.com/gihadalgahmi2025/evaluation.git

# أو من مجلد محلي
bench get-app /path/to/evaluation
```

### 3. إنشاء موقع وتثبيت التطبيق

```bash
bench new-site mysite.local --db-root-password <pwd> --admin-password <pwd>
bench --site mysite.local install-app evaluation
```

### 4. تهيئة البيانات الأساسية

```bash
bench --site mysite.local execute evaluation.bootstrap.bootstrap
```

هذا الأمر يُنشئ تلقائياً:

- ✅ 7 أدوار ومستويات الصلاحيات
- ✅ الحقول المخصصة (نطاق الوحدة، التصنيف الأمني)
- ✅ 6 سير عمل مع الحالات والانتقالات
- ✅ البيانات المرجعية: 12 تشكيلاً، 15 نوع وحدة، 11 وضعاً قتالياً، 10 أصناف تموين، 16 رتبة، 18 نوع هدف...
- ✅ 6 مساحات عمل (Workspaces)
- ✅ 17 تقريراً
- ✅ 4 لوحات معلومات + 11 رسماً بيانياً + 19 بطاقة رقم
- ✅ 5 قوالب طباعة
- ✅ 4 إشعارات + قالبا بريد

### 5. بيانات تجريبية (اختياري)

```bash
bench --site mysite.local execute evaluation.bootstrap.install_demo_data
```

### 6. التشغيل

```bash
bench start
# أو للتطوير
bench --site mysite.local serve --port 8000
```

ثم افتح `http://mysite.local:8000` وسجّل الدخول.

---

## بنية التطبيق

```
evaluation/
├── evaluation/                      # حزمة التطبيق
│   ├── hooks.py                     # الإعدادات والـ hooks
│   ├── setup.py                     # دورة حياة التثبيت
│   ├── setup_data.py                # البيانات المرجعية الثابتة
│   ├── bootstrap.py                 # أمر التهيئة الشامل
│   ├── demo_data.py                 # البيانات التجريبية
│   ├── utils.py                     # دوال مشتركة
│   ├── permissions.py               # الصلاحيات على مستوى الصف
│   ├── mixins.py                    # MasterRecord / CodeMixin
│   ├── tasks.py                     # المهام المجدولة
│   ├── boot.py                      # بيانات boot للواجهة
│   ├── workspace_builder.py         # بناء المساحات واللوحات
│   ├── report_builder.py            # بناء التقارير (17)
│   ├── dashboard_builder.py         # واجهة للوحات
│   ├── notification_builder.py      # الإشعارات وقوالب البريد
│   ├── print_builder.py             # قوالب الطباعة
│   ├── patches/                     # ترقيات المخطط
│   │   └── v0_1/
│   ├── tests/                       # اختبارات الوحدة
│   ├── evaluation/                  # وحدة التقييم
│   ├── reconnaissance/              # وحدة الاستطلاع
│   ├── order_of_battle/             # وحدة ترتيب المعركة
│   ├── targeting/                   # وحدة الأهداف
│   ├── operations/                  # وحدة العمليات
│   ├── personnel/                   # وحدة الأفراد
│   ├── public/js/                   # جافاسكربت الواجهة
│   └── translations/                # ar.csv / en.csv
├── patches.txt
├── pyproject.toml
└── README.md
```

---

## الوحدات الست

### 1️⃣ Evaluation — التقييم (11 DocType)

وحدة القياس والترتيب.

| DocType | النوع | الوصف |
| --- | --- | --- |
| Evaluation Unit | شجرة | هيكل الوحدات الصديقة — يتحكم بالصلاحيات |
| Evaluation Criteria | رئيسي | معيار واحد (رقمي/نسبة/منطقي/معادلة) بوزن |
| Evaluation Criteria Group | رئيسي | مجموعة معايير قابلة لإعادة الاستخدام |
| Evaluation Score Card | معاملات | بطاقة تقييم بدرجات موزونة وترتيب تلقائي |
| Evaluation Score Line | جدول فرعي | سطر درجة داخل البطاقة |
| Combat Power Weight | رئيسي | أوزان مؤشر القوة القتالية |
| Combat Effectiveness Type | رئيسي | أنواع الفعالية القتالية |
| Combat Effectiveness Line | جدول فرعي | قياس فعالية داخل التشكيل |
| Readiness Metric | رئيسي | مقياس جاهزية |
| Readiness Line | جدول فرعي | سطر جاهزية داخل التشكيل |
| Evaluation Branch / Designation / Salutation | رئيسي | جداول مرجعية |

**نموذج التقييم:**

```
الدرجة الموزونة = تطبيع(القيمة) × الوزن
الدرجة الكلية = (Σ الدرجات الموزونة ÷ Σ الأوزان) × 100
```

- **رقمي**: `القيمة ÷ القيمة القصوى` (محدودة بـ 1)
- **نسبة**: `القيمة ÷ 100`
- **منطقي**: `1` أو `0`
- **معادلة**: تُقيَّم في بيئة معزولة (بدون `eval` — AST آمن فقط)

---

### 2️⃣ Reconnaissance — الاستطلاع (16 DocType)

وحدة جمع المعلومات الميدانية.

| DocType | النوع | الوصف |
| --- | --- | --- |
| Daily Activities | معاملات | **قلب التطبيق** — رصد ميداني واحد |
| Activity Side | شجرة | جهة الرصد (بري، جوي، تقني...) |
| Activity Worker | رئيسي | المراقب الميداني |
| Activity Reporter | رئيسي | مصدر التقرير |
| Public Activity | رئيسي | نوع النشاط المرصود (يستنتج الوضع القتالي) |
| Daily Activity Readiness Line | جدول فرعي | تغيّر الجاهزية |
| Daily Activity Spread Line | جدول فرعي | تغيّر الانتشار |
| Daily Activity Task Link | جدول فرعي | ربط بمهمة عملياتية |
| Governorate / Governorate Directorate | رئيسي | التقسيم الإداري |
| Insulation | معاملات | العزل الجغرافي |
| Geolocation | رئيسي | إحداثيات على الخريطة |
| Geographic / Tactic / Management Spread | جدول فرعي | نقاط انتشار (جغرافي، تكتيكي، إداري) |
| Movement Method | جدول فرعي | طرق الحركة ونقاط الطريق |

**تأثير الرصد عند الاعتماد:**

1. تحديث `last_daily_activity` و`last_observed` للوحدة
2. استنتاج الوضع القتالي من نوع النشاط
3. تعديل نسبة القوة حسب تغيّر الجاهزية
4. إنشاء تقرير استخباري تلقائياً (إن مُفعّل)
5. ترشيح هدف تلقائياً (إن مُفعّل)

---

### 3️⃣ Order Of Battle — ترتيب المعركة (17 DocType)

الوحدة الأكبر — تصف قوة العدو بالكامل.

| DocType | النوع | الوصف |
| --- | --- | --- |
| **Force Arrangement** | شجرة | **مركز التطبيق** — تشكيل القوات المرصود (67 حقلاً) |
| Enemy Order of Battle | شجرة | الهيكل النظري لترتيب معركة العدو |
| Military Divisions | شجرة | الفرق العسكرية |
| Division Size | رئيسي | حجم التشكيل (فريق → جيش) |
| Division Type | رئيسي | نوع التشكيل (مشاة، مدرع، مدفعية...) |
| Combat Posture | رئيسي | الوضع القتالي (هجوم، دفاع، كمين...) |
| Engagement Force | رئيسي | قوة الاشتباك |
| Reinforcement Force | رئيسي | قوة التعزيز |
| Fire Support Unit | جدول فرعي | وحدة إسناد ناري |
| Fire Support Unit Type | رئيسي | نوع الإسناد الناري |
| Supply Class | رئيسي | صنف التموين (I – X) |
| Logistics Line | جدول فرعي | سطر إمداد |
| Ammunition Line | جدول فرعي | سطر ذخيرة |
| Training | جدول فرعي | دليل مستوى التدريب |

**مؤشر القوة القتالية (CPI):**

```
CPI = (الجاهزية × 0.35) + (الإمداد × 0.25) + (الذخيرة × 0.20) + (القوة × 0.20)
```

الأوزان قابلة للتعديل من `Combat Power Weight`.

---

### 4️⃣ Targeting — الأهداف (6 DocType)

| DocType | النوع | الوصف |
| --- | --- | --- |
| **Target** | معاملات | الهدف مع تحليل CARVER وتقييم الأضرار |
| Target Category | شجرة | تصنيف هرمي للأهداف |
| Target Type | رئيسي | نوع الهدف (يحدد الأهداف الحساسة زمنياً TST) |
| Target Carver Line | جدول فرعي | بند من بنود CARVER الستة |
| Target Bda Line | جدول فرعي | تقييم أضرار بعد الضربة |
| Target Status Log | جدول فرعي | سجل تغيّرات الحالة (تدقيق كامل) |

**حساب درجة الأولوية:**

```
الدرجة = [ (CARVER ÷ الحد الأقصى) × 0.45
         + الثقة × 0.25
         + موثوقية المصدر × 0.20
         + حداثة المعلومات × 0.10 ] × 100

ثم تُطابَق مع نطاق الأولوية المعلنة:
  حرج  90–100 | عالي 70–89 | متوسط 40–69 | منخفض 0–39
```

**CARVER:** الحرجة، إمكانية الوصول، قابلية الاستعادة، القابلية للاستهداف، الأثر، سهولة التعرف — كل بند 1–5.

---

### 5️⃣ Operations — العمليات (15 DocType)

| DocType | النوع | الوصف |
| --- | --- | --- |
| Operation Order | معاملات | أمر عمليات مع مراحل ومهام وإسناد |
| Operation Phase | جدول فرعي | مرحلة |
| Operation Task | جدول فرعي | مهمة |
| Operation Force Assignment | جدول فرعي | إسناد قوة |
| Operation Target Link | جدول فرعي | ربط هدف |
| Intel Report | معاملات | تقرير استخباري بتصنيف الأميرالية (A–F × 1–6) |
| Situation Report | معاملات | تقرير موقف مع لقطة حالة |
| Situation Snapshot Line | جدول فرعي | سطر لقطة |
| Situation Activity Link | جدول فرعي | ربط نشاط |
| Situation Layer | رئيسي | طبقة عرض الموقف |
| Threat Assessment | معاملات | تقييم تهديد (قدرة × نية × فرصة) |
| Threat Assessment Line | جدول فرعي | سطر تهديد |
| Casualty Report | معاملات | تقرير خسائر |
| Casualty Personnel/Equipment Line | جدول فرعي | خسائر أفراد/عتاد |

**تصنيف الأميرالية:**

```
الثقة = (درجة الموثوقية × 0.6) + (درجة المصداقية × 0.4)

الموثوقية: A=1.0  B=0.85  C=0.70  D=0.50  E=0.30  F=0.10
المصداقية: 1=1.0  2=0.90  3=0.75  4=0.55  5=0.35  6=0.15
```

**تقييم التهديد:**

```
درجة السطر = (القدرة×0.5 + النية×0.3 + الفرصة×0.2) ÷ 5 × 100
التهديد الكلي = (متوسط الدرجات × 0.7) + (أعلى درجة × 0.3)

≥ 75 حرج | ≥ 55 عالٍ | ≥ 30 متوسط | < 30 منخفض
```

**انتقالات أمر العمليات:**

```
مخطط ──► معتمد ──► نشط ──► مكتمل
  │         │        │
  └─────────┴────────┴──► ملغى
       └──► مؤجل ──┘
```

---

### 6️⃣ Personnel — الأفراد (10 DocType)

| DocType | النوع | الوصف |
| --- | --- | --- |
| **Personality** | شجرة | ملف شخص (عسكري/مدني) — 67 حقلاً |
| Personality Dependent | جدول فرعي | التابعون |
| Army Chief | جدول فرعي | القادة المرصودون داخل التشكيل |
| Employee Education | جدول فرعي | المؤهل العلمي |
| Employee External Work History | جدول فرعي | الخبرة العملية |
| Military Rank | رئيسي | الرتب العسكرية |
| Gender | رئيسي | الجنس |
| Evaluation Branch | رئيسي | فرع التقييم |
| Evaluation Designation | رئيسي | المسمى الوظيفي |
| Evaluation Salutation | رئيسي | اللقب |

**الميزات:**
- تكوين الاسم الكامل تلقائياً
- توليد رقم شخصية ثابت من الاسم/الرقم المالي
- منع الدوران في سلسلة التسلسل القيادي
- مخطط تنظيمي متداخل (org chart)

---

## الوحدات الفنية (DocTypes)

### توزيع الـ 75 DocType

| الوحدة | العدد |
| --- | --- |
| Evaluation | 11 |
| Reconnaissance | 16 |
| Order Of Battle | 17 |
| Targeting | 6 |
| Operations | 15 |
| Personnel | 10 |
| **الإجمالي** | **75** |

### أنماط التسمية

| DocType | النمط | مثال |
| --- | --- | --- |
| Target | Naming Series | `TGT-00001` |
| Intel Report | Naming Series | `INT-202600001` |
| Daily Activities | Naming Series | `DA-ACTIV-00001` |
| Situation Report | Naming Series | `SITREP-202600001` |
| Operation Order | Naming Series | `OPORD-202600001` |
| Casualty Report | Naming Series | `CAS-202600001` |
| Threat Assessment | Naming Series | `THR-202600001` |
| Personality | Naming Series | `HR-EMP-00001` |
| Force Arrangement | حسب الحقل | `3rd Armoured Brigade` |
| Enemy Order of Battle | حسب الحقل | `Northern Corps` |
| Evaluation Score Card | تعبير | `ESC-00001` |

---

## منطق العمل

### دورة حياة الرصد

```python
# عند الحفظ (validate)
- منع الرصد المستقبلي
- منع التكرار (وحدة + تاريخ + موضوع)
- استنتاج الوضع القتالي والجغرافيا من الوحدة
- حساب تغيّر القوة من سطور الجاهزية

# عند الاعتماد (on_submit)
- تحديث الوحدة المرصودة
- إنشاء تقرير استخباري (إن مُفعّل)
- ترشيح هدف (إن مُفعّل)

# عند الإلغاء (on_cancel)
- إزالة مؤشرات الوحدة حتى لا تبقى معلّقة
```

### دورة حياة الهدف

```python
# عند الحفظ
- التحقق من التواريخ والإحداثيات
- وراثة وحدة التقييم من المصدر
- الأهداف الحساسة زمنياً ← رفع الأولوية إلى "عالي" + نافذة صلاحية 6 ساعات
- حساب درجة الأولوية
- تسجيل تغيّر الحالة في Status Log

# قبل الاعتماد
- منع اعتماد هدف No-Strike
- إلزام الإحداثيات
- إلزام مصدر استخباري
```

### نقاط الاتصال (Hooks)

```python
doc_events = {
    "*":                        validate_common_rules
    "Evaluation Criteria":      validate_criteria
    "Evaluation Criteria Group": validate_group
    "Evaluation Score Card":    compute_total → refresh_ranking
    "Force Arrangement":        validate_force
    "Enemy Order of Battle":    validate_ob
    "Daily Activities":         validate_activity → after_submit_activity → on_cancel_activity
    "Intel Report":             validate_intel
    "Target":                   validate_target → log_status_change
    "Operation Order":          validate_operation
    "Situation Report":         validate_sitrep
    "Casualty Report":          compute_casualties
    "Personality":              set_full_name
    "Threat Assessment":        compute_threat
}
```

---

## الأمان والصلاحيات

### ثلاث طبقات

**1. صلاحيات الأدوار**

| الدور | الصلاحية |
| --- | --- |
| Evaluation User | قراءة/إنشاء ضمن وحدته |
| Evaluation Manager | كل الوحدات، قراءة/كتابة |
| Evaluation Commander | اعتماد العمليات والبطاقات |
| Evaluation Intel Officer | الاستخبارات، التحقق من الأهداف |
| Evaluation Ops Officer | أوامر العمليات |
| Evaluation Fires Officer | الإسناد الناري والأهداف |
| Evaluation Logistics Officer | الإمداد والجاهزية |

**2. نطاق الوحدة (Row Level)**

```
المستخدم ← evaluation_units (حقل مخصص)
        ← أو Personality.evaluation_unit
        ← تُوسَّع لتشمل الوحدات الفرعية
```

- مدير النظام والمدير: لا قيود
- غيرهم: يرى وحدته ووحداتها الفرعية فقط

**3. التصنيف الأمني**

الحقول الحساسة (`latitude`, `longitude`, `mgrs`) تُخفى عمّن لا يملك دور الاستخبارات:

```python
from evaluation.permissions import scrub_doc_for_user
scrub_doc_for_user(doc)  # يحجب الإحداثيات في مكانها
```

### الحماية من الحذف

كل جدول مرجعي يمنع حذفه إذا كان مستخدماً:

```
لا يمكن حذف "Artillery 155mm": مرتبط بـ Ammunition Line (AL-0001، AL-0002).
عطّله بدلاً من ذلك.
```

---

## سير العمل (Workflows)

| Workflow | DocType | الحالات |
| --- | --- | --- |
| Daily Activity Review | Daily Activities | مسودة ← مراجعة ← مُصادق ← معتمد ← مغلق |
| Intel Report Review | Intel Report | نفس المسار |
| Target Approval | Target | مسودة ← مُصادق ← معتمد ← مغلق |
| Operation Order Approval | Operation Order | مسودة ← مراجعة ← معتمد ← نشط ← مغلق |
| Situation Report Review | Situation Report | مسودة ← مراجعة ← مُصادق ← معتمد |
| Threat Assessment Review | Threat Assessment | مسودة ← مراجعة ← مُصادق ← معتمد |

---

## التقارير واللوحات

### 17 تقريراً

| # | التقرير | الوحدة |
| --- | --- | --- |
| 1 | Unit Ranking — ترتيب الوحدات | Evaluation |
| 2 | Combat Power Index — مؤشر القوة | Evaluation |
| 3 | Criteria Weights — أوزان المعايير | Evaluation |
| 4 | Observation Coverage — تغطية الرصد | Reconnaissance |
| 5 | Observer Performance — أداء المراقبين | Reconnaissance |
| 6 | Order of Battle Summary — ملخص ترتيب المعركة | Order Of Battle |
| 7 | Force Comparison — مقارنة القوات | Order Of Battle |
| 8 | Logistics Readiness — جاهزية الإمداد | Order Of Battle |
| 9 | CARVER Matrix — مصفوفة كارفر | Targeting |
| 10 | BDA Register — سجل تقييم الأضرار | Targeting |
| 11 | Target Priority Board — لوحة الأولويات | Targeting |
| 12 | Intel Source Reliability — موثوقية المصادر | Operations |
| 13 | Situation Overview — نظرة على الموقف | Operations |
| 14 | Threat Matrix — مصفوفة التهديدات | Operations |
| 15 | Casualty Summary — ملخص الخسائر | Operations |
| 16 | Personnel Roster — كشف الأفراد | Personnel |
| 17 | Rank Distribution — توزيع الرتب | Personnel |

جميعها **Query Reports** قابلة للتصفية والتصدير إلى Excel/CSV.

### 6 مساحات عمل

`Evaluation` · `Reconnaissance` · `Order Of Battle` · `Targeting` · `Operations` · `Personnel`

كل مساحة تحتوي: اختصارات، بطاقات روابط، رسوم بيانية، وبطاقات أرقام.

### 4 لوحات معلومات

`Recon Overview` · `Targeting Board` · `Evaluation Overview` · `Operations Overview`

### 5 قوالب طباعة

`Target Dossier` · `Daily Observation Report` · `Situation Report` · `Intel Report` · `Force Arrangement Summary`

كلها بترويسة تصنيف أمني وتنسيق WeasyPrint جاهز للـ PDF.

---

## واجهة برمجة التطبيقات

### REST API (تلقائي لكل DocType)

```bash
# قائمة الأهداف الحرجة
GET /api/resource/Target?filters=[["priority","=","Critical"]]&fields=["name","target_name","priority_score"]

# هدف معيّن
GET /api/resource/Target/TGT-00001

# إنشاء رصد
POST /api/resource/Daily Activities
```

### دوال مخصصة

```python
# إحصائيات اللوحة
GET /api/method/evaluation.utils.get_dashboard_stats?evaluation_unit=Alpha Sector

# بحث سريع في القوات
GET /api/method/evaluation.utils.search_enemy_forces?txt=Armoured

# تسلسل الوحدة
GET /api/method/evaluation.utils.get_unit_hierarchy?force_arrangement=3rd Armoured Brigade

# اختبار معيار تقييم (بدون حفظ)
POST /api/method/evaluation.evaluation.doctype.evaluation_criteria.evaluation_criteria.test_expression

# تشغيل تقرير
POST /api/method/evaluation.report_builder.run_report
  {"report_name": "CARVER Matrix", "filters": {}}
```

---

## المهام المجدولة

| التكرار | المهمة | الوظيفة |
| --- | --- | --- |
| كل ساعة | `recompute_priority_scores` | تحديث درجات أولوية الأهداف مع تقادم المعلومات |
| يومياً | `expire_targets` | إغلاق الأهداف المنتهية الصلاحية |
| يومياً | `refresh_observation_freshness` | تعليم الوحدات غير المرصودة كـ "مشكوك" |
| يومياً | `rebuild_readiness_snapshots` | إعادة حساب مؤشر القوة القتالية |
| أسبوعياً | `flag_stale_intel` | تنبيه بالتقارير الاستخبارية غير المستثمرة (14 يوماً) |
| شهرياً | `archive_cancelled_docs` | تقرير بالمستندات الملغاة الجاهزة للأرشفة |
| 06:00 يومياً | `morning_intel_digest` | ملخص بريدي لكل وحدة تقييم |

---

## التطوير

### إضافة معيار تقييم جديد

```bash
bench --site mysite.local console
```

```python
import frappe
crit = frappe.get_doc({
    "doctype": "Evaluation Criteria",
    "criterion_name": "Mobility Score",
    "criterion_type": "Percentage",
    "applies_to": "Force Arrangement",
    "weight": 20,
    "max_value": 100,
    "is_active": 1,
})
crit.insert()
```

### إضافة معادلة مخصصة

```python
frappe.get_doc({
    "doctype": "Evaluation Criteria",
    "criterion_name": "Logistics Efficiency",
    "criterion_type": "Formula",
    "formula_expression": "(value / max_value) * 0.8 + weight * 0.2",
    "applies_to": "Force Arrangement",
    "weight": 15,
    "max_value": 100,
}).insert()
```

المعادلات تُقيَّم في بيئة معزولة — المتغيرات المتاحة: `value`, `max_value`, `weight`, `min`, `max`, `round`, `abs`.

### إعادة بناء الواجهة بعد تعديل الكود

```bash
bench --site mysite.local execute evaluation.bootstrap.bootstrap
bench --site mysite.local clear-cache
```

### إضافة حقل جديد

1. أضفه إلى ملف الـ DocType JSON
2. `bench --site mysite.local migrate`
3. أضف الترجمة في `evaluation/translations/ar.csv`

---

## الاختبارات

```bash
# كل الاختبارات
bench --site mysite.local run-tests --app evaluation

# وحدة معينة
bench --site mysite.local run-tests --module evaluation.tests.test_core
```

**النتيجة الحالية: 175 اختباراً — كلها ناجحة ✅**

تغطي الاختبارات:
- الدوال المشتركة (تطبيع، نسب، مسافات، MGRS)
- محرك التقييم (تطبيع الأنواع الأربعة، أمان المعادلات)
- منطق الأولوية ونطاقاتها
- مقياس التهديد
- الصلاحيات ونطاق الوحدة
- 54 اختبار تحقق مخطط لكل DocType

---

## استكشاف الأخطاء

| المشكلة | الحل |
| --- | --- |
| `Module import failed for X` | تأكد من وجود `__init__.py` في مجلد الـ DocType؛ نظّف `__pycache__` |
| `LinkValidationError` عند التثبيت | نفّذ `bench --site <site> migrate` أولاً لإنشاء الجداول |
| الأصول لا تظهر | `bench build --app evaluation` ثم `bench clear-cache` |
| المساحات فارغة | `bench --site <site> execute evaluation.bootstrap.bootstrap` |
| `DuplicateEntryError` عند install-app | احذف سجل `Module Def` القديم أو استخدم `--force` |

---

## الترخيص

MIT — انظر `license.txt`

## المساهمة

المستودع: <https://github.com/gihadalgahmi2025/evaluation>
