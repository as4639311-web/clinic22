"""Demo data so the app is usable on first run (SEED_DEMO_DATA=true).

Demo login:  demo@tawazun.app  /  Demo@1234
"""
from __future__ import annotations

from .core.clock import utcnow

import random
from datetime import date, datetime, time, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from .core.logging import get_logger
from .core.security import encrypt_text, hash_password
from .models import (
    Appointment, Assessment, Content, Goal, MedicalHistory, Measurement, Message, Notification,
    Plan, PlanItem, PlanLog, ShareGrant, Specialist, User,
)

log = get_logger("seed")
DEMO_EMAIL = "demo@tawazun.app"
DEMO_PASSWORD = "Demo@1234"

SPECIALISTS = [
    # name_ar, name_en, title_ar, title_en, service, gender, languages, modes, rating, years
    ("د. سارة الهاشمي", "Dr. Sara Al Hashimi", "أخصائية نفسية إكلينيكية", "Clinical Psychologist", "mental", "female", ["ar", "en"], ["in_person", "video", "audio"], 4.9, 11),
    ("د. يوسف الكعبي", "Dr. Yousef Al Kaabi", "معالج نفسي — العلاج المعرفي السلوكي", "Psychotherapist — CBT", "mental", "male", ["ar", "en"], ["in_person", "video"], 4.8, 8),
    ("أ. خالد المنصوري", "Khalid Al Mansoori", "مدرب أداء بدني معتمد", "Certified Performance Coach", "fitness", "male", ["ar", "en"], ["in_person", "video"], 4.8, 7),
    ("أ. لمى الشامسي", "Lama Al Shamsi", "مدربة لياقة وتأهيل", "Fitness & Conditioning Coach", "fitness", "female", ["ar", "en"], ["in_person", "video"], 4.7, 5),
    ("د. ريم العلي", "Dr. Reem Al Ali", "طبيبة طب رياضي", "Sports Medicine Physician", "sports_medicine", "female", ["ar", "en"], ["in_person", "video"], 4.9, 12),
    ("د. أحمد الظاهري", "Dr. Ahmed Al Dhaheri", "أخصائي إصابات رياضية", "Sports Injury Specialist", "sports_medicine", "male", ["ar"], ["in_person"], 4.6, 9),
    ("أ. نورة السويدي", "Noura Al Suwaidi", "أخصائية تغذية علاجية", "Clinical Dietitian", "nutrition", "female", ["ar", "en"], ["in_person", "video", "audio"], 4.9, 10),
    ("أ. عمر الحمادي", "Omar Al Hammadi", "أخصائي تغذية رياضية", "Sports Nutritionist", "nutrition", "male", ["ar", "en"], ["video", "audio"], 4.7, 6),
    ("أ. هند المرزوقي", "Hind Al Marzouqi", "مثقفة صحية", "Health Educator", "education", "female", ["ar", "en"], ["video", "audio", "in_person"], 4.8, 8),
]


def _at(days: int, hour: int, minute: int = 0) -> datetime:
    return datetime.combine(date.today() + timedelta(days=days), time(hour, minute))


def seed(db: Session) -> None:
    if db.scalar(select(User).where(User.email == DEMO_EMAIL)):
        return
    rnd = random.Random(42)

    sps = []
    for row in SPECIALISTS:
        n_ar, n_en, t_ar, t_en, svc, g, langs, modes, rating, years = row
        sps.append(Specialist(
            name_ar=n_ar, name_en=n_en, title_ar=t_ar, title_en=t_en, service=svc, gender=g, languages=langs,
            modes=modes, rating=rating, years=years,
            bio_ar=f"{t_ar} بخبرة {years} سنوات، يركّز على خطط واقعية ومتابعة قريبة.",
            bio_en=f"{t_en} with {years} years of experience, focused on realistic plans and close follow-up.",
        ))
    db.add_all(sps)
    db.flush()
    sara, yousef, khalid, lama, reem, ahmed, noura, omar, hind = sps

    u = User(email=DEMO_EMAIL, password_hash=hash_password(DEMO_PASSWORD), full_name="مريم أحمد",
             phone="+971500000000", birth_date=date(1993, 5, 12), gender="female", locale="ar", theme="system",
             file_number="TW-104823")
    db.add(u)
    db.flush()
    db.add(MedicalHistory(
        user_id=u.id, blood_type="O+",
        chronic_conditions=[{"ar": "نقص فيتامين د", "en": "Vitamin D deficiency"}],
        medications=[{"ar": "فيتامين د 50,000 وحدة أسبوعياً", "en": "Vitamin D 50,000 IU weekly"}],
        allergies=[{"ar": "الفول السوداني", "en": "Peanuts"}],
        surgeries=[],
        injuries=[{"ar": "التواء كاحل أيمن (2024)", "en": "Right ankle sprain (2024)"}],
        family_history=[{"ar": "سكري النوع الثاني (الأب)", "en": "Type 2 diabetes (father)"}],
    ))

    def series(domain, kind, n_ar, n_en, unit, values, every_days, rng, lower=False, sp=None, notes=None):
        k = len(values)
        for i, v in enumerate(values):
            note = notes if (notes and i == k - 1) else (None, None)
            db.add(Assessment(user_id=u.id, domain=domain, kind=kind, name_ar=n_ar, name_en=n_en, value=v, unit=unit,
                              range_low=rng[0], range_high=rng[1], lower_is_better=lower,
                              taken_at=utcnow() - timedelta(days=every_days * (k - 1 - i) + 2),
                              specialist_id=sp.id if sp else None, note_ar=note[0], note_en=note[1]))

    series("mental", "scale", "مقياس الاكتئاب PHQ-9", "PHQ-9", "", [14, 12, 10, 8, 7, 6], 14, (0, 4), True, sara,
           ("تحسّن واضح ومستمر. نواصل تمارين التنشيط السلوكي.", "Clear, steady improvement. Continue behavioural activation."))
    series("mental", "scale", "مقياس القلق GAD-7", "GAD-7", "", [11, 9, 8, 6], 21, (0, 4), True, sara)
    series("physical", "test", "اللياقة القلبية VO2 max", "VO2 max", "ml/kg/min", [31, 32.5, 34, 35, 36.5, 38], 14, (35, 50), False, khalid,
           ("أفضل نتيجة لك حتى الآن. نرفع شدة تمارين الفترات تدريجياً.", "Your best result so far. We'll gradually raise interval intensity."))
    series("physical", "test", "تمرين الضغط (تكرار)", "Push-ups (reps)", "reps", [8, 11, 14, 17], 21, (15, 40), False, khalid)
    series("nutrition", "body", "نسبة الدهون", "Body fat", "%", [33.5, 32.6, 31.8, 30.9, 30.1, 29.4], 14, (21, 31), True, noura,
           ("دخلتِ النطاق الصحي. حافظي على البروتين في كل وجبة.", "You're now in the healthy range. Keep protein in every meal."))
    series("nutrition", "lab", "فيتامين د", "Vitamin D", "ng/mL", [16, 24], 60, (30, 100), False, reem,
           ("ما زال أقل من الطبيعي؛ نكمل المكمل ونعيد الفحص بعد 8 أسابيع.", "Still below normal; continue the supplement and retest in 8 weeks."))
    series("general", "lab", "الهيموغلوبين", "Hemoglobin", "g/dL", [12.6, 13.1], 60, (12, 15.5), False, reem)
    series("general", "lab", "السكر التراكمي HbA1c", "HbA1c", "%", [5.6, 5.4], 60, (4, 5.7), True, reem)

    # Weight + daily check-ins
    for i in range(0, 84, 3):
        # i = days ago: from ~78.2 kg twelve weeks ago down to ~74 kg today
        db.add(Measurement(user_id=u.id, kind="weight", value=round(74.0 + i * 0.05 + rnd.uniform(-0.3, 0.3), 1),
                           recorded_at=utcnow() - timedelta(days=i)))
    for i in range(1, 15):
        t = utcnow() - timedelta(days=i)
        base = 3 if i > 7 else 4
        db.add(Measurement(user_id=u.id, kind="mood", value=min(5, max(1, base + rnd.choice([-1, 0, 0, 1]))), recorded_at=t))
        db.add(Measurement(user_id=u.id, kind="energy", value=min(5, max(1, base + rnd.choice([-1, 0, 1]))), recorded_at=t))
        db.add(Measurement(user_id=u.id, kind="sleep_hours", value=round(rnd.uniform(5.8, 8.0), 1), recorded_at=t))

    db.add_all([
        Goal(user_id=u.id, domain="nutrition", title_ar="الوصول إلى 72 كجم", title_en="Reach 72 kg",
             start_value=78.5, target_value=72, current_value=74.1, unit="kg", target_date=date.today() + timedelta(days=60)),
        Goal(user_id=u.id, domain="physical", title_ar="رفع VO2 max إلى 40", title_en="Raise VO2 max to 40",
             start_value=31, target_value=40, current_value=38, unit="ml/kg/min", target_date=date.today() + timedelta(days=45)),
        Goal(user_id=u.id, domain="mental", title_ar="PHQ-9 أقل من 5", title_en="PHQ-9 below 5",
             start_value=14, target_value=4, current_value=6, unit="", target_date=date.today() + timedelta(days=30)),
        Goal(user_id=u.id, domain="general", title_ar="النوم 7 ساعات يومياً", title_en="Sleep 7 hours a day",
             start_value=5.5, target_value=7, current_value=6.6, unit="h", target_date=date.today() + timedelta(days=30)),
    ])

    def appt(sp, days, hour, mode, status, summary=None, reason=None):
        a = Appointment(user_id=u.id, specialist_id=sp.id, service=sp.service, starts_at=_at(days, hour), mode=mode,
                        status=status, reason=reason,
                        summary=(encrypt_text(summary) if sp.service == "mental" else summary) if summary else None)
        db.add(a)
        return a

    appt(sara, -42, 18, "video", "completed", "جلسة تقييم أولي. وُضعت أهداف علاجية: النوم، والتنشيط السلوكي.")
    appt(khalid, -35, 17, "in_person", "completed", "اختبار لياقة أساسي وبدء برنامج 3 أيام أسبوعياً.")
    appt(noura, -30, 16, "video", "completed", "قياس InBody. خطة غذائية بعجز 400 سعرة وبروتين 1.6 جم/كجم.")
    appt(sara, -14, 18, "video", "completed", "تحسن في المزاج والنوم. إضافة تمرين تنفس يومي 5 دقائق.")
    appt(reem, -10, 11, "in_person", "completed", "مراجعة التحاليل: فيتامين د ما زال منخفضاً. متابعة الكاحل: سليم.")
    appt(khalid, -7, 17, "in_person", "completed", "رفع الأحمال 10%. أداء ممتاز في تمارين الفترات.")
    appt(noura, 2, 17, "video", "booked", reason="متابعة الخطة الغذائية")
    appt(khalid, 4, 18, "in_person", "booked", reason="إعادة اختبار اللياقة")
    appt(sara, 6, 19, "video", "booked", reason="جلسة متابعة")
    db.add(ShareGrant(user_id=u.id, specialist_id=noura.id, sections=["nutrition", "physical", "goals"],
                      expires_at=utcnow() + timedelta(days=20)))
    db.add(ShareGrant(user_id=u.id, specialist_id=khalid.id, sections=["physical", "history"],
                      expires_at=utcnow() + timedelta(days=12)))

    # Plans
    def plan(sp, kind, t_ar, t_en, items, weeks_ago=4):
        p = Plan(user_id=u.id, specialist_id=sp.id, kind=kind, title_ar=t_ar, title_en=t_en,
                 start_date=date.today() - timedelta(weeks=weeks_ago), end_date=date.today() + timedelta(weeks=8))
        for wd, a, e, da, de, mins in items:
            p.items.append(PlanItem(weekday=wd, title_ar=a, title_en=e, detail_ar=da, detail_en=de, duration_min=mins))
        db.add(p)
        return p

    training = plan(khalid, "training", "برنامج اللياقة — المستوى 2", "Fitness program — Level 2", [
        (0, "قوة الجزء العلوي", "Upper-body strength", "ضغط 3×12، تجديف بالدمبل 3×10، ضغط كتف 3×10", "Push-ups 3×12, dumbbell rows 3×10, shoulder press 3×10", 40),
        (2, "تمارين الفترات", "Interval training", "إحماء 5 د، ثم 8 جولات: 40 ث سريع / 80 ث هادئ", "5-min warm-up, then 8 rounds: 40s fast / 80s easy", 30),
        (5, "قوة الجزء السفلي", "Lower-body strength", "قرفصاء 3×12، اندفاع 3×10 لكل رجل، جسر 3×15", "Squats 3×12, lunges 3×10 each leg, glute bridge 3×15", 40),
        (6, "مشي نشِط", "Brisk walk", "مشي 35 دقيقة بوتيرة تسمح بالكلام بصعوبة", "35-minute walk at a pace where talking is hard", 35),
    ])
    meals = [
        ("فطور: شوفان بالحليب والتوت", "Breakfast: oats with milk and berries", "40 جم شوفان + 200 مل حليب + حفنة توت", "40 g oats + 200 ml milk + a handful of berries", None),
        ("غداء: صدر دجاج مشوي وأرز بني وسلطة", "Lunch: grilled chicken, brown rice, salad", "150 جم دجاج + 3/4 كوب أرز + سلطة كبيرة", "150 g chicken + ¾ cup rice + large salad", None),
        ("عشاء: لبنة وخضار وخبز أسمر", "Dinner: labneh, vegetables, wholegrain bread", "بدون فول سوداني — حساسية", "No peanuts — allergy", None),
    ]
    nutrition = plan(noura, "nutrition", "خطة غذائية — عجز معتدل", "Nutrition plan — moderate deficit",
                     [(wd, *m) for wd in range(7) for m in meals])
    mental = plan(sara, "mental", "تمارين يومية للهدوء والنوم", "Daily calm & sleep practice", [
        (wd, "تنفس 4-7-8 لمدة 5 دقائق", "4-7-8 breathing, 5 minutes", "قبل النوم: شهيق 4، حبس 7، زفير 8 — كرريها 4 مرات",
         "Before bed: inhale 4, hold 7, exhale 8 — repeat 4 times", 5) for wd in range(7)
    ] + [(wd, "نشاط ممتع صغير", "One small enjoyable activity", "اختاري نشاطاً واحداً من قائمتك ودوّني شعورك بعده",
          "Pick one activity from your list and note how you feel afterwards", 20) for wd in (1, 3, 5)], weeks_ago=2)
    db.flush()

    # ~70–80% adherence over the last 3 weeks, today left open
    for p, rate in ((training, 0.8), (nutrition, 0.72), (mental, 0.85)):
        for back in range(1, 22):
            d = date.today() - timedelta(days=back)
            if d < p.start_date:
                continue
            for it in p.items:
                if it.weekday == d.weekday() and rnd.random() < rate:
                    db.add(PlanLog(item_id=it.id, user_id=u.id, day=d, done=True))

    for sp, who, body, ago in (
        (noura, "specialist", "أهلاً مريم، راجعت سجل وجباتك هذا الأسبوع — التزام رائع! هل نجرب وجبة سحور أخف؟", 26),
        (noura, "user", "شكراً! نعم، أحتاج اقتراحات خفيفة.", 25),
        (khalid, "specialist", "تذكير: أحضري حذاء جري مريحاً لاختبار اللياقة القادم.", 5),
    ):
        db.add(Message(user_id=u.id, specialist_id=sp.id, sender=who, body=encrypt_text(body),
                       created_at=utcnow() - timedelta(hours=ago), read=who == "user"))

    db.add_all([
        Notification(user_id=u.id, kind="result", title_ar="نتيجة جديدة: نسبة الدهون", title_en="New result: body fat",
                     body_ar="29.4% — ضمن النطاق الصحي", body_en="29.4% — in the healthy range", created_at=utcnow() - timedelta(days=2)),
        Notification(user_id=u.id, kind="plan", title_ar="تم تحديث خطة اللياقة", title_en="Fitness plan updated",
                     body_ar="رفع الأحمال 10% بدءاً من هذا الأسبوع", body_en="Loads raised 10% from this week", created_at=utcnow() - timedelta(days=7)),
    ])

    content = [
        ("mental", "article", "كيف تهدّئ القلق في 5 دقائق", "Calm anxiety in 5 minutes", "تقنيات تنفس وتأريض بسيطة تستطيع استخدامها في أي مكان.", "Simple breathing and grounding techniques you can use anywhere.", 4),
        ("mental", "video", "ما هو العلاج المعرفي السلوكي؟", "What is CBT?", "شرح مبسّط لكيفية عمل العلاج المعرفي السلوكي ولماذا هو فعّال.", "A plain explanation of how CBT works and why it's effective.", 6),
        ("mental", "tip", "نصيحة اليوم: دوّن ثلاثة أشياء جيدة", "Tip: write down three good things", "عادة مسائية صغيرة ترتبط بتحسن المزاج مع الوقت.", "A small evening habit linked with better mood over time.", 1),
        ("fitness", "article", "تمارين الفترات للمبتدئين", "Interval training for beginners", "كيف تبدأ بأمان، وكم مرة في الأسبوع، وكيف تعرف أنك تتقدم.", "How to start safely, how often, and how to know you're progressing.", 5),
        ("fitness", "video", "الإحماء الصحيح في 7 دقائق", "A proper warm-up in 7 minutes", "روتين إحماء يقلل خطر الإصابة ويحسّن الأداء.", "A warm-up routine that lowers injury risk and improves performance.", 7),
        ("sports_medicine", "article", "العودة للرياضة بعد التواء الكاحل", "Returning to sport after an ankle sprain", "مراحل التأهيل وعلامات الاستعداد للعودة.", "Rehab stages and signs you're ready to return.", 6),
        ("sports_medicine", "tip", "الثلج أم الحرارة؟", "Ice or heat?", "متى تستخدم كل منهما بعد الإصابة الرياضية.", "When to use each after a sports injury.", 2),
        ("nutrition", "article", "البروتين: كم تحتاج فعلاً؟", "Protein: how much do you really need?", "احسب احتياجك اليومي ووزّعه على وجباتك.", "Work out your daily need and spread it across meals.", 5),
        ("nutrition", "article", "التغذية في رمضان", "Eating well in Ramadan", "سحور يُشبع وإفطار متوازن دون إرهاق.", "A filling suhoor and a balanced iftar without the slump.", 6),
        ("nutrition", "tip", "اشرب ماءً قبل الوجبة", "Drink water before meals", "كوب ماء قبل الأكل يساعد على الشبع والترطيب.", "A glass of water before eating helps fullness and hydration.", 1),
        ("education", "article", "كيف تقرأ نتائج تحاليلك", "How to read your lab results", "ماذا تعني النطاقات الطبيعية ولماذا تختلف بين المختبرات.", "What reference ranges mean and why they vary between labs.", 5),
        ("education", "video", "النوم وصحتك", "Sleep and your health", "لماذا يؤثر النوم على المزاج والوزن والأداء الرياضي.", "Why sleep affects mood, weight and athletic performance.", 8),
    ]
    for svc, typ, ta, te, sa, se, mins in content:
        db.add(Content(service=svc, type=typ, title_ar=ta, title_en=te, summary_ar=sa, summary_en=se, minutes=mins,
                       body_ar=f"{sa}\n\nهذا محتوى تثقيفي عام ولا يغني عن استشارة أخصائي. يمكنك حجز جلسة لمناقشة حالتك.",
                       body_en=f"{se}\n\nThis is general education and does not replace a specialist consultation. You can book a session to discuss your situation."))
    db.commit()
    log.info("demo data seeded — login %s / %s", DEMO_EMAIL, DEMO_PASSWORD)
