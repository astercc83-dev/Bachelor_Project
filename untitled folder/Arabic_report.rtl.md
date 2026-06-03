# تقرير: محاكاة نظام اقتناء البيانات (DAQ Simulation)
**المشروع:** تطوير واجهة Python لنظام PXI لاقتناء البيانات  
**الطالب:** سمير الشربيني  
**المشرف:** د. محمد عميرة  
**التاريخ:** مايو 2026

---

## 1. الهدف من المحاكاة

قبل الحصول على وصول فعلي لجهاز PXI، تم بناء محاكاة كاملة بلغة Python تُجسّد المشكلة الجوهرية في مشروع الاقتناء الحقيقي، وهي:

> **كيف نقرأ البيانات من جهاز سريع جداً (PXI) ونعالجها ونحفظها في نفس الوقت، دون أن نخسر أي بيانات؟**

---

## 2. المكونات الأساسية التي تم تعلّمها وتطبيقها

### 2.1 الـ Thread (خيط التنفيذ)
- **التعريف:** وحدة تنفيذ مستقلة تعمل بالتوازي مع وحدات أخرى داخل نفس البرنامج.
- **المكتبة المستخدمة:** `threading` (مدمجة في Python)
- **الفائدة:** تشغيل عمليات متعددة في نفس الوقت بدلاً من التسلسل.

```python
import threading

def my_task():
    print("بدأت الشغل")

thread = threading.Thread(target=my_task)
thread.start()
```

---

### 2.2 الـ Queue (الصندوق المشترك)
- **التعريف:** بنية بيانات آمنة للخيوط (thread-safe) تعمل على مبدأ FIFO (أول من يدخل أول من يخرج).
- **المكتبة المستخدمة:** `queue` (مدمجة في Python)
- **الفائدة:** تمرير البيانات بأمان بين الـ threads دون تعارض.

```python
import queue

my_box = queue.Queue()
my_box.put("sample 0")   # إضافة عنصر
data = my_box.get()       # سحب عنصر
```

---

### 2.3 الـ Event (حدث الإيقاف)
- **التعريف:** علامة مشتركة بين الـ threads تُستخدم للإشارة إلى وقت الإيقاف.
- **الأوامر الأساسية:**
  - `stop_event.set()` ← رفع علامة الإيقاف
  - `stop_event.is_set()` ← هل علامة الإيقاف مرفوعة؟

```python
stop_event = threading.Event()

# داخل الـ thread:
while not stop_event.is_set():
    # استمر في العمل

# من البرنامج الرئيسي:
stop_event.set()  # أوقف كل الـ threads
```

---

## 3. المشكلة الرئيسية: Buffer Overflow

### 3.1 ما هو الـ Buffer Overflow؟
عندما يكون الـ Reader (القارئ) أسرع من الـ Processor (المعالج)، تمتلئ الـ Queue ولا يجد Reader مكاناً لوضع البيانات الجديدة، فتُفقد هذه البيانات للأبد.

**مثال توضيحي:**
```
Reader: يقرأ كل 0.5 ثانية   ← سريع
Processor: يعالج كل 1 ثانية ← بطيء

النتيجة: Queue تمتلئ → Overflow → فقدان البيانات!
```

### 3.2 كيف تم اكتشاف الـ Buffer Overflow؟
استخدمنا `queue.full()` للتحقق قبل كل إضافة:

```python
if queue_1.full():
    lost_samples += 1
    print(f"Overflow! ضاع sample {i}")
else:
    queue_1.put(f"sample {i}")
```

---

## 4. معمارية الحل: نمط Producer-Consumer

### 4.1 الهيكل العام
```
Reader Thread → Queue 1 → Processor Thread → Queue 2 → Saver Thread
      ↑                         ↑                          ↑
  stop_event               stop_event                  stop_event
```

### 4.2 دور كل Thread

| الـ Thread | شغله | السرعة |
|-----------|------|--------|
| Reader | يقرأ البيانات ويضعها في Queue 1 | سريع (0.5 ثانية) |
| Processor | يأخذ من Queue 1، يعالج، يضع في Queue 2 | أبطأ (1 ثانية) |
| Saver | يأخذ من Queue 2 ويحفظ في ملف | متوسط |

### 4.3 لماذا Queue وليس تمرير مباشر؟
لأن سرعات الـ threads مختلفة. الـ Queue تعمل كـ "صدمة ماصّة" تستوعب الفرق في السرعة وتمنع توقف الـ Reader انتظاراً للـ Processor.

---

## 5. المشاكل التي واجهناها وكيف تم حلها

### المشكلة 1: الـ file كان فارغاً عند الحفظ
**السبب:** Python يجمع البيانات في الـ RAM أولاً (Buffering) ثم يكتبها دفعةً واحدة.  
**الحل:** استخدام `file.flush()` بعد كل كتابة لإجبار Python على الكتابة الفورية.

```python
file.write(data + "\n")
file.flush()  # اكتب على القرص فوراً!
```

---

### المشكلة 2: الـ Saver يتوقف قبل أن يُفرغ Queue 2
**السبب:** الـ Saver كان يتوقف فور رفع `stop_event`، حتى لو كانت Queue 2 لا تزال تحتوي بيانات.  
**الحل:** تعديل شرط الـ while ليستمر حتى تفرغ Queue 2.

```python
# قبل التعديل (خطأ):
while not stop_event.is_set():

# بعد التعديل (صح):
while not stop_event.is_set() or not queue_1.empty() or not queue_2.empty():
```

---

### المشكلة 3: الـ Processor يتوقف قبل أن يُفرغ Queue 1
**السبب:** نفس مشكلة الـ Saver. الـ Processor كان يتوقف فور رفع `stop_event` ويترك بيانات في Queue 1.  
**الحل:** نفس الحل، تعديل شرط الـ while.

```python
while not stop_event.is_set() or not queue_1.empty():
    try:
        data = queue_1.get(timeout=0.5)
        # معالجة البيانات
    except:
        pass
```

---

### المشكلة 4: الـ Queue لا تفرغ بعد الإيقاف
**السبب:** بعد رفع `stop_event`، كان البرنامج الرئيسي ينتهي قبل أن تُفرغ الـ queues.  
**الحل:** إضافة حلقة انتظار حتى تفرغ الـ queues.

```python
while not queue_1.empty():
    time.sleep(0.1)
while not queue_2.empty():
    time.sleep(0.1)
```

---

### المشكلة 5: غلطات الأقواس المتكررة
**السبب:** كتابة `queue.full` و`stop_event.is_set` بدون أقواس `()`.  
**الشرح:** بدون الأقواس، Python لا ينفّذ الدالة بل يُرجع الدالة نفسها (دائماً True).  
**القاعدة:**

```python
# غلط:
if queue_1.full:       ← دائماً True!
if stop_event.is_set:  ← دائماً True!

# صح:
if queue_1.full():       ← ينفّذ الدالة ويُرجع True أو False
if stop_event.is_set():  ← ينفّذ الدالة ويُرجع True أو False
```

---

## 6. الكود الكامل النهائي

```python
import threading
import queue
import time

# الـ Queues والمتغيرات المشتركة
queue_1 = queue.Queue(maxsize=20)
queue_2 = queue.Queue()
stop_event = threading.Event()
lost_samples = 0
total_read = 0
total_processed = 0


def reader():
    """يقرأ البيانات ويضعها في Queue 1"""
    global lost_samples, total_read
    i = 0
    while not stop_event.is_set():
        if queue_1.full():
            lost_samples += 1
            print(f"Overflow - sample {i} lost. Total lost: {lost_samples}")
        else:
            queue_1.put(f"sample {i}")
            total_read += 1
            print(f"Reader: read sample {i}")
        i += 1
        time.sleep(0.5)


def processor():
    """يأخذ من Queue 1، يعالج، يضع في Queue 2"""
    global total_processed
    while not stop_event.is_set() or not queue_1.empty():
        try:
            data = queue_1.get(timeout=0.5)
            total_processed += 1
            print(f"Processor: processing {data}")
            queue_2.put(data)
            time.sleep(1)
        except:
            pass


def saver():
    """يأخذ من Queue 2 ويحفظ في ملف"""
    file = open("data.txt", "w")
    while not stop_event.is_set() or not queue_1.empty() or not queue_2.empty():
        try:
            data = queue_2.get(timeout=0.5)
            file.write(data + "\n")
            file.flush()
        except:
            pass
    file.close()
    print("Saver: file closed")


# إنشاء وتشغيل الـ threads
thread_reader = threading.Thread(target=reader)
thread_processor = threading.Thread(target=processor)
thread_saver = threading.Thread(target=saver)

thread_reader.start()
thread_processor.start()
thread_saver.start()

# انتظار المستخدم
input("Press Enter to stop...\n")
stop_event.set()

# انتظار تفريغ الـ queues
while not queue_1.empty():
    time.sleep(0.1)
while not queue_2.empty():
    time.sleep(0.1)

# انتظار انتهاء الـ threads
thread_reader.join()
thread_processor.join()
thread_saver.join()

# الإحصائيات النهائية
total_attempted = total_read + lost_samples
print(f"\n=== النتائج النهائية ===")
print(f"إجمالي المحاولات:  {total_attempted}")
print(f"إجمالي اللي اتقرأ: {total_read}")
print(f"إجمالي اللي اتشغّل: {total_processed}")
print(f"إجمالي الـ overflow: {lost_samples}")
print(f"التحقق: {total_attempted} = {total_read} + {lost_samples} → {total_read + lost_samples == total_attempted}")
```

---

## 7. النتائج والإحصائيات

عند تشغيل البرنامج مع:
- **Reader:** كل 0.5 ثانية
- **Processor:** كل 1 ثانية  
- **Queue 1:** سعة 20 sample

| الحالة | النتيجة |
|--------|---------|
| Reader أسرع من Processor | Overflow يحدث ❌ |
| Processor أسرع من Reader | لا يوجد Overflow ✅ |
| Queue كبيرة | يؤخّر الـ Overflow بس لا يمنعه |

---

## 8. الخلاصة والدروس المستفادة

1. **Multithreading ضروري** لأنظمة اقتناء البيانات عالية السرعة.
2. **الـ Queue** هي الحل الأمثل لتمرير البيانات بين الـ threads.
3. **Buffer Overflow** يحدث عندما يكون Reader أسرع من Processor.
4. **الإغلاق النظيف** للبرنامج يتطلب التأكد من تفريغ جميع الـ queues أولاً.
5. **الأقواس `()`** ضرورية دائماً عند استدعاء أي دالة في Python.

---

## 9. الخطوة القادمة

استبدال السطر التالي في الـ reader:

```python
# المحاكاة (دلوقتي):
queue_1.put(f"sample {i}")

# الكود الحقيقي (عند الوصول للـ PXI):
data = task.read()
queue_1.put(data)
```

باقي الكود يبقى كما هو! ✅
