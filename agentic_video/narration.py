"""
The script: Hindi narration (spoken) + English subtitles (shown).

Every line is one voice clip:

    ("key", "Hindi narration (spoken)", "English subtitle (shown)")

Write the Hindi exactly as it should be SPOKEN, and the English with the same
number of sentences (sentence i of the subtitle is shown while sentence i of
the Hindi is spoken). Word-level pronunciation tweaks go in
agentic_video/pronunciation.py.

After editing:  .venv/bin/python -m tools.build all -j 5
(only changed Hindi lines are re-voiced; subtitle-only edits cost no credits)
"""

LANGUAGE = "hi"

SECTIONS: dict[str, dict] = {
    # ------------------------------------------------------------------ 01
    "s01": {
        "chapter": ("01", "Introduction"),
        "lines": [
            ("s01_01", "मान लीजिए, कोई प्रोग्राम चलाते समय अचानक एक Error आ गया।",
             "Imagine you're running a program, and suddenly an error appears."),
            ("s01_02", "आपने एक AI से पूछा, इस Error का मतलब क्या है?",
             "You ask an AI: what does this error mean?"),
            ("s01_03", "AI ने अच्छे से समझा दिया कि दिक्कत कहाँ हो सकती है।",
             "The AI explains nicely where the problem might be."),
            ("s01_04", "लेकिन उस दिक्कत को ठीक करने का काम, अभी भी आपके ही हाथ में रह गया।",
             "But the job of actually fixing it is still left to you."),
            ("s01_05", "अब यही स्थिति, थोड़ा अलग तरीके से सोचिए।",
             "Now picture the same situation a little differently."),
            ("s01_06", "आपने एक AI Agent से कहा, Error को ढूँढो, उसकी वजह समझो, और उसे ठीक कर दो।",
             "You tell an AI agent: find the error, understand its cause, and fix it."),
            ("s01_07", "Agent खुद प्रोजेक्ट की Files खोलकर देख रहा है, Commands चला रहा है।",
             "The agent opens the project's files by itself and runs commands."),
            ("s01_08", "उसे एक Error मिला, उसे देखकर उसने Code ठीक किया, और फिर से जाँच की।",
             "It hits an error, fixes the code based on it, and then checks again."),
            ("s01_09", "पहला AI हमें जानकारी देता है। और दूसरा, लक्ष्य पूरा करने के लिए खुद काम करता है।",
             "The first AI gives us information. The second one takes action itself to reach the goal."),
            ("s01_10", "यही फ़र्क Agentic AI का मूल विचार है। लेकिन यह असल में मुमकिन कैसे होता है? चलिए, बिल्कुल शुरुआत से देखते हैं।",
             "That difference is the core idea of Agentic AI. But how is this actually possible? Let's start from the very beginning."),
        ],
    },
    # ------------------------------------------------------------------ 02
    "s02": {
        "chapter": ("02", "What is an AI model?"),
        "lines": [
            ("s02_01", "Agent को समझने से पहले, हमें समझना होगा कि AI Model असल में क्या है।",
             "Before we understand agents, we need to understand what an AI model really is."),
            ("s02_02", "AI Model एक ऐसा प्रोग्राम है, जिसने बहुत बड़ी मात्रा में डेटा से सीखा है।",
             "An AI model is a program that has learned from a huge amount of data."),
            ("s02_03", "जो Models भाषा के साथ काम करते हैं, उन्हें Large Language Model कहते हैं, छोटे में LLM।",
             "Models that work with language are called Large Language Models, or LLMs for short."),
            ("s02_04", "इन्होंने अनगिनत लेख पढ़कर सीखा है कि इंसान कैसे सवाल पूछते हैं, समझाते हैं, और जवाब देते हैं।",
             "By reading countless texts, they've learned how people ask questions, explain things, and give answers."),
            ("s02_05", "इसके काम करने का तरीका बहुत आसान है। आप कुछ लिखकर देते हैं, इसे Input कहते हैं।",
             "The way it works is very simple. You give it some text, which is called the input."),
            ("s02_06", "Model उस Input को पढ़ता है, और समझने की कोशिश करता है।",
             "The model reads that input and tries to understand it."),
            ("s02_07", "Model जो कुछ भी एक साथ सामने देख पाता है, उसे Context कहते हैं, यानी संदर्भ।",
             "Everything the model can see at once is called its context."),
            ("s02_08", "फिर Model नया टेक्स्ट बनाकर वापस देता है। यही है Output।",
             "Then the model generates new text and gives it back. That's the output."),
            ("s02_09", "GPT, Claude, Gemini, ये सभी Large Language Model के उदाहरण हैं।",
             "GPT, Claude and Gemini are all examples of large language models."),
            ("s02_10", "लेकिन एक बात पर ध्यान दीजिए। Model खुद सिर्फ़ टेक्स्ट बनाता है। यह अपने आप कोई File नहीं खोलता, कोई प्रोग्राम भी नहीं चलाता।",
             "But notice one thing. On its own, a model only produces text. It doesn't open files or run programs by itself."),
            ("s02_11", "तो फिर असली काम करने की ताकत आती कहाँ से है?",
             "So where does the power to actually do things come from?"),
        ],
    },
    # ------------------------------------------------------------------ 03
    "s03": {
        "chapter": ("03", "What is an AI agent?"),
        "lines": [
            ("s03_01", "यहीं पर आता है AI Agent।",
             "This is where the AI agent comes in."),
            ("s03_02", "AI Agent एक ऐसा System है, जो एक AI Model का इस्तेमाल करके, किसी लक्ष्य की ओर काम करता है।",
             "An AI agent is a system that uses an AI model to work toward a goal."),
            ("s03_03", "यह फ़ैसले लेता है, Tools की मदद से काम करता है, नतीजे देखता है, और फिर तय करता है कि आगे क्या करना है।",
             "It makes decisions, acts using tools, looks at the results, and then decides what to do next."),
            ("s03_04", "एक Agent के पाँच बुनियादी हिस्से होते हैं। चलिए, एक-एक करके देखते हैं।",
             "An agent has five basic parts. Let's look at them one by one."),
            ("s03_05", "पहला है Goal, यानी लक्ष्य। हम असल में क्या हासिल करना चाहते हैं।",
             "First, the goal. What are we actually trying to achieve?"),
            ("s03_06", "दूसरा है Model। यही Agent का सोचने वाला हिस्सा है, जो सोचता है और फ़ैसले लेता है।",
             "Second, the model. This is the agent's thinking part, which reasons and makes decisions."),
            ("s03_07", "तीसरा है Tools, यानी औज़ार। इन्हीं के ज़रिए Agent बाहरी Systems के साथ काम कर पाता है।",
             "Third, tools. Through them, the agent can work with outside systems."),
            ("s03_08", "चौथा है Environment, यानी माहौल। वह दुनिया या System, जिसके अंदर Agent काम कर रहा है, जैसे आपका कंप्यूटर, या कोई प्रोजेक्ट।",
             "Fourth, the environment. The world or system the agent works inside, like your computer or a project."),
            ("s03_09", "और पाँचवाँ है Feedback, यानी प्रतिक्रिया। कोई काम करने के बाद, जो जानकारी वापस आती है।",
             "And fifth, feedback. The information that comes back after an action."),
            ("s03_10", "ध्यान दीजिए, Model यहाँ पूरे System का सिर्फ़ एक हिस्सा है। सिर्फ़ एक AI Model, और एक पूरा AI Agent, एक ही चीज़ नहीं हैं।",
             "Notice that the model is just one part of the whole system. An AI model on its own and a complete AI agent are not the same thing."),
        ],
    },
    # ------------------------------------------------------------------ 04
    "s04": {
        "chapter": ("04", "Chatbot vs AI agent"),
        "lines": [
            ("s04_01", "अब तुलना करते हैं। एक आम Chatbot, और एक AI Agent।",
             "Now let's compare. A regular chatbot, and an AI agent."),
            ("s04_02", "Chatbot को एक सवाल मिलता है।",
             "A chatbot receives a question."),
            ("s04_03", "वह उस सवाल का एक जवाब बनाता है।",
             "It generates an answer to that question."),
            ("s04_04", "और जवाब आपको लौटा देता है। बस, काम खत्म।",
             "And it hands the answer back to you. That's it, job done."),
            ("s04_05", "दूसरी तरफ़, Agent को मिलता है एक लक्ष्य।",
             "An agent, on the other hand, receives a goal."),
            ("s04_06", "वह तय करता है कि लक्ष्य तक पहुँचने के लिए क्या-क्या करना होगा।",
             "It works out what needs to be done to reach that goal."),
            ("s04_07", "काम के लिए सही Tool चुनता है।",
             "It picks the right tool for the job."),
            ("s04_08", "फिर असली काम करता है।",
             "Then it performs the actual work."),
            ("s04_09", "काम के नतीजे को देखता है।",
             "It observes the result of that work."),
            ("s04_10", "और जब तक लक्ष्य पूरा न हो जाए, या इंसान की मदद की ज़रूरत न पड़े, ऐसे ही चलता रहता है।",
             "And it keeps going like this until the goal is reached, or until it needs a human's help."),
            ("s04_11", "एक ज़रूरी बात। Agent से भी आप Chat करके ही बात कर सकते हैं।",
             "One important point. You can talk to an agent through a chat window too."),
            ("s04_12", "इसलिए फ़र्क इसमें नहीं है कि वह दिखता कैसा है। फ़र्क यह है कि System खुद काम कर सकता है या नहीं, और लक्ष्य की ओर बढ़ सकता है या नहीं।",
             "So the difference isn't how it looks. The difference is whether the system can take action itself and move toward a goal."),
        ],
    },
    # ------------------------------------------------------------------ 05
    "s05": {
        "chapter": ("05", "How does an agent work?"),
        "lines": [
            ("s05_01", "अब आते हैं सबसे ज़रूरी हिस्से पर। एक Agent असल में काम कैसे करता है?",
             "Now for the most important part. How does an agent actually work?"),
            ("s05_02", "इसके केंद्र में एक चक्र है, जिसे Agent Loop कहते हैं।",
             "At its core is a cycle called the agent loop."),
            ("s05_03", "पहला कदम, Goal लेना। यूज़र Agent को एक निर्देश देता है।",
             "Step one: receive the goal. The user gives the agent an instruction."),
            ("s05_04", "जैसे मान लीजिए, बताओ कल दिल्ली में बारिश होगी या नहीं।",
             "For example: tell me whether it will rain in Delhi tomorrow."),
            ("s05_05", "दूसरा कदम, Decide, यानी फ़ैसला। Model तय करता है कि अब अगला काम क्या होगा।",
             "Step two: decide. The model decides what the next action should be."),
            ("s05_06", "यहाँ उसने सोचा, चलो मौसम की एक Website देखते हैं।",
             "Here it thinks: let's check a weather website."),
            ("s05_07", "तीसरा कदम, Act, यानी काम। Agent एक Tool से वह काम करता है। यहाँ उसने Browser से Website खोली।",
             "Step three: act. The agent uses a tool to do that work. Here, it opens the website with a browser."),
            ("s05_08", "चौथा कदम, Observe, यानी देखना। Tool एक नतीजा लौटाता है। लेकिन पता चला, Page तो लोड ही नहीं हुआ।",
             "Step four: observe. The tool returns a result. But it turns out the page didn't even load."),
            ("s05_09", "पाँचवाँ कदम, Evaluate, यानी जाँच। Agent देखता है, क्या लक्ष्य पूरा हुआ? नहीं, अभी नहीं।",
             "Step five: evaluate. The agent checks: has the goal been reached? No, not yet."),
            ("s05_10", "इसलिए चक्र फिर से शुरू होता है।",
             "So the loop starts again."),
            ("s05_11", "इस बार Agent ने तय किया कि वह कोई दूसरी Website आज़माएगा।",
             "This time, the agent decides to try a different website."),
            ("s05_12", "Browser ने फिर काम किया। और इस बार नतीजा आया, बारिश की संभावना अस्सी प्रतिशत।",
             "The browser works again. And this time the result comes back: an eighty percent chance of rain."),
            ("s05_13", "जाँच करने पर पता चला कि लक्ष्य पूरा हो गया। इसलिए Agent ने आपको जवाब बता दिया।",
             "Checking again, the goal has been reached. So the agent gives you the answer."),
            ("s05_14", "ध्यान दीजिए, Agent को शुरू से सारे कदम पता नहीं थे। हर नतीजे को देखकर, उसने अपना अगला फ़ैसला बदला।",
             "Notice that the agent didn't know every step from the start. After each result, it adjusted its next decision."),
            ("s05_15", "यही है Agent Loop। Decide, Act, Observe, Evaluate, और ज़रूरत हो तो, फिर से।",
             "That's the agent loop. Decide, act, observe, evaluate, and if needed, again."),
        ],
    },
    # ------------------------------------------------------------------ 06
    "s06": {
        "chapter": ("06", "Why agents need tools"),
        "lines": [
            ("s06_01", "हम बार-बार Tools की बात कर रहे हैं। लेकिन Agent को Tools की ज़रूरत क्यों है?",
             "We keep talking about tools. But why does an agent need them?"),
            ("s06_02", "क्योंकि Model खुद सिर्फ़ टेक्स्ट बना सकता है। बाहरी दुनिया के साथ काम करने के लिए, उसे Tools चाहिए।",
             "Because a model on its own can only produce text. To work with the outside world, it needs tools."),
            ("s06_03", "जैसे, Filesystem। इससे Files पढ़ी जा सकती हैं, नई File बनाई जा सकती है, और Files बदली जा सकती हैं।",
             "Take the filesystem. With it, files can be read, new files created, and existing files changed."),
            ("s06_04", "Terminal से Commands और प्रोग्राम चलाए जा सकते हैं।",
             "With a terminal, commands and programs can be run."),
            ("s06_05", "Browser से अलग-अलग Websites से जानकारी लाई जा सकती है।",
             "With a browser, information can be fetched from websites."),
            ("s06_06", "API से किसी दूसरी Service के साथ बात की जा सकती है, जैसे मौसम या मैप की Service।",
             "With an API, it can talk to another service, like a weather or maps service."),
            ("s06_07", "और Database से व्यवस्थित जानकारी खोजी और बदली जा सकती है।",
             "And with a database, structured information can be searched and updated."),
            ("s06_08", "यहाँ एक ज़रूरी फ़र्क है।",
             "There's an important distinction here."),
            ("s06_09", "Model तय करता है कि कौन सा Tool चाहिए, और क्या काम करना है। वह सिर्फ़ एक अनुरोध भेजता है।",
             "The model decides which tool is needed and what should be done. It only sends a request."),
            ("s06_10", "असली काम Tool खुद करता है। फिर नतीजा Model के पास वापस भेजता है।",
             "The tool does the actual work. Then it sends the result back to the model."),
            ("s06_11", "आसान शब्दों में, Model है दिमाग, और Tool हैं हाथ।",
             "Put simply, the model is the brain, and the tools are the hands."),
        ],
    },
    # ------------------------------------------------------------------ 07
    "s07": {
        "chapter": ("07", "Real example: fixing a bug"),
        "lines": [
            ("s07_01", "अब सब कुछ एक साथ देखते हैं, एक असली उदाहरण में।",
             "Now let's see everything together in a real example."),
            ("s07_02", "यूज़र ने Agent से कहा, प्रोग्राम Crash हो रहा है, वजह ढूँढकर इसे ठीक कर दो।",
             "The user tells the agent: the program is crashing, find the cause and fix it."),
            ("s07_03", "यह प्रोग्राम एक छोटा सा हिसाब वाला ऐप है, जो कुछ संख्याओं का औसत निकालता है।",
             "The program is a small calculator app that computes the average of some numbers."),
            ("s07_04", "सबसे पहले Agent ने प्रोजेक्ट की Files की लिस्ट देखी।",
             "First, the agent looks at the list of files in the project."),
            ("s07_05", "नाम देखकर लगता है कि हिसाब का काम stats नाम की File में होता है। इसलिए Agent ने उसे खोलकर Code पढ़ा।",
             "From the names, the calculation seems to live in stats.py. So the agent opens it and reads the code."),
            ("s07_06", "फिर उसने Terminal में प्रोग्राम के Tests चलाए, ताकि दिक्कत खुद देखी जा सके।",
             "Then it runs the program's tests in the terminal to see the problem for itself."),
            ("s07_07", "Test फ़ेल हो गया। Error आया, Zero Division Error, यानी शून्य से भाग।",
             "A test fails. The error is ZeroDivisionError, a division by zero."),
            ("s07_08", "Agent ने Error को ध्यान से देखा। लिस्ट में कोई संख्या न हो, तो प्रोग्राम शून्य से भाग देने की कोशिश करता है।",
             "The agent looks closely at the error. When the list has no numbers, the program tries to divide by zero."),
            ("s07_09", "इसलिए उसने Code में एक छोटा सा बदलाव किया। लिस्ट खाली हो, तो पहले ही शून्य लौटा दो।",
             "So it makes a small change to the code. If the list is empty, return zero right away."),
            ("s07_10", "फिर उसने दोबारा Tests चलाए।",
             "Then it runs the tests again."),
            ("s07_11", "इस बार सारे Tests पास हो गए। Agent ने जाँच करके देखा कि लक्ष्य पूरा हो गया।",
             "This time all the tests pass. The agent checks and confirms the goal is reached."),
            ("s07_12", "आखिर में Agent ने बताया कि दिक्कत क्या थी, क्या बदला, और अब सब कुछ ठीक है।",
             "Finally, the agent reports what the problem was, what it changed, and that everything works now."),
            ("s07_13", "देखा आपने? Goal, Model, Tools, Environment और Feedback, पाँचों हिस्सों ने यहाँ एक साथ काम किया। और हर कदम पर, Agent Loop बार-बार घूमा।",
             "See? Goal, model, tools, environment and feedback, all five parts worked together here. And at every step, the agent loop went around again."),
        ],
    },
    # ------------------------------------------------------------------ 08
    "s08": {
        "chapter": ("08", "Reality check: not magic"),
        "lines": [
            ("s08_01", "लेकिन एक बात याद रखना ज़रूरी है। AI Agent ताकतवर है, लेकिन जादू नहीं।",
             "But one thing is important to remember. AI agents are powerful, but they're not magic."),
            ("s08_02", "Agent गलत फ़ैसले ले सकता है।",
             "An agent can make wrong decisions."),
            ("s08_03", "Tools का गलत इस्तेमाल कर सकता है।",
             "It can use tools incorrectly."),
            ("s08_04", "यहाँ तक कि ज़रूरी Files या जानकारी बदल सकता है, या मिटा भी सकता है।",
             "It can even change, or delete, important files or data."),
            ("s08_05", "कभी-कभी एक ही काम बार-बार करके, एक चक्र में फँस सकता है।",
             "Sometimes it repeats the same action and gets stuck in a loop."),
            ("s08_06", "इसलिए Agent को चाहिए Permission, यानी इजाज़त। चाहिए Safeguard, यानी सुरक्षा के इंतज़ाम। और चाहिए इंसान की निगरानी।",
             "That's why an agent needs permissions. It needs safeguards. And it needs human oversight."),
            ("s08_07", "Agent कौन से काम कर सकता है, और कौन से नहीं, वह सीमा हम ही तय करते हैं।",
             "We are the ones who set the boundary of what an agent can and cannot do."),
            ("s08_08", "याद रखिए, AI को जितनी ज़्यादा ताकत देंगे, उस ताकत को काबू में रखने की ज़िम्मेदारी भी उतनी ही ज़्यादा होगी।",
             "Remember: the more power you give an AI, the greater your responsibility to keep that power under control."),
        ],
    },
    # ------------------------------------------------------------------ 09
    "s09": {
        "chapter": ("09", "Conclusion"),
        "lines": [
            ("s09_01", "अब आप समझ गए हैं कि AI Agent असल में क्या है, यह कैसे काम करता है, और एक आम Chatbot से इसका फ़र्क कहाँ है।",
             "Now you understand what an AI agent really is, how it works, and how it differs from a regular chatbot."),
            ("s09_02", "लेकिन अभी तक हमने Agentic AI के सिर्फ़ बिल्कुल बुनियादी विचार देखे हैं।",
             "But so far, we've only seen the most basic ideas of Agentic AI."),
            ("s09_03", "आने वाले Lessons में हम और गहराई में जाएँगे।",
             "In the upcoming lessons, we'll go much deeper."),
            ("s09_04", "समझेंगे कि Agent के अंदर का Architecture कैसे काम करता है, Tool Integration, Context Management, Memory, Planning, और Agentic Systems कैसे बनाए जाते हैं।",
             "We'll see how an agent's architecture works, along with tool integration, context management, memory, planning, and how agentic systems are built."),
            ("s09_05", "और सिर्फ़ इतना ही नहीं, हम खुद Websites और Apps बनाना भी सीखेंगे।",
             "And that's not all: we'll also learn to build websites and apps ourselves."),
            ("s09_06", "यह था Agentic AI सीखने के हमारे सफ़र की बस शुरुआत।",
             "This was just the beginning of our journey into Agentic AI."),
        ],
    },
}


def all_lines():
    """Yield (section, key, subtitle_text, spoken_text) for every line in order."""
    for sec, data in SECTIONS.items():
        for key, spoken, subtitle in data["lines"]:
            yield sec, key, subtitle, spoken
