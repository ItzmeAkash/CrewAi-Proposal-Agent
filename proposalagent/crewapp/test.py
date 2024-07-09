# # from langchain_openai import ChatOpenAI

# # llm = ChatOpenAI(
# #     model="gpt-3.5-turbo",
# #     temperature=0.9
# # )

# # def rewrite_text(input_text: str, prompt_suffix: str) -> str:
# #     prompt = input_text + prompt_suffix
# #     response = llm.invoke(prompt)
# #     return response.content

# # # Initial input text
# # input_text = """

# # """
# # prompt_suffix = ' I want this to more explain each and every thing.'

# # # Get the rewritten text
# # rewritten_text = rewrite_text(input_text, prompt_suffix)
# # print(rewritten_text)

# # # Change the input text and get a new response
# # input_text = """
# # New text that you want to rewrite and explain...
# # """
# # rewritten_text = rewrite_text(input_text, prompt_suffix)
# # print(rewritten_text)



# # #########


# # from langchain_openai import ChatOpenAI

# # llm = ChatOpenAI(
# #     model="gpt-3.5-turbo",
# #     temperature=0.9
# # )

# # def rewrite_text(input_text: str, prompt_suffix: str) -> str:
# #     prompt = input_text + prompt_suffix
# #     response = llm.invoke(prompt)
# #     return response.content

# # # Initial input text
# # input_text = """

# # """
# # prompt_suffix = ' I want this to more explain each and every thing.'

# # # Get the rewritten text
# # rewritten_text = rewrite_text(input_text, prompt_suffix)
# # print(rewritten_text)

# # # Change the input text and get a new response


# result = {
#     "proposal_result": "hey proposal",
#     "google_result": "hey google"
# }

# input_text = result.get("proposal_result")

# print(input_text)


from openai import OpenAI
from langchain_openai import ChatOpenAI

# Initialize the model
llm = ChatOpenAI(
    model="gpt-4o",
    temperature=0.6
)

def rewrite_text(input_text: str, prompt_suffix: str) -> str:
    # Construct the prompt with clear instructions
    prompt = f"""
    You are an AI assistant here to help with anything requested.

    Input text: {input_text}

    Prompt to change the input text: {prompt_suffix}

    Please combine the input text and the generated result, updating only as specified.
    """

    # print(prompt)
    response = llm.invoke(prompt)
    return response.content.strip()

# Define your input text
input_text = """
**[Your Company Name]**

**[Your Company Logo]**

---

**Executive Summary**

Our proposal aims to introduce Boost Reading, a student-led supplemental reading curriculum, to enhance literacy instruction and support student learning across all instructional tiers. Boost Reading offers a comprehensive range of features designed to cater to individual skill development, address remediation needs, and extend core instruction. By leveraging Boost Reading's innovative approach to literacy instruction, educators can effectively support students in improving their reading abilities and achieving academic success.

---

**Table of Contents**

1. Introduction
2. Program Description
3. Eligibility Criteria
4. Application Process
5. Evaluation Criteria
6. Budget Information
7. Conclusion

---

**1. Introduction**

The U.S. Embassy Ethiopia PD Request for Statement of Interest provides a unique opportunity to introduce Boost Reading, a research-based and standards-aligned program, to support literacy development and enhance educational outcomes. This proposal outlines a comprehensive public engagement program that aligns with the objectives of the funding opportunity and aims to strengthen cultural ties between the U.S. and Ethiopia.

---

**2. Program Description**

Boost Reading is a student-led supplemental reading curriculum that offers additional support and reinforcement across all instructional tiers. It serves as a digital assistant in literacy instruction, extending core instruction, addressing remediation needs, and adapting activities for individual skill development. The program employs highly adaptive technology to create individual skill maps for each student, catering to students reading below, at, or above grade level. With Boost Reading, educators can provide personalized practice, benchmark assessments, and engaging narrative experiences to enhance student learning and promote literacy growth.

---

**3. Eligibility Criteria**

- Applicants: U.S. and Ethiopian not-for-profits, educational institutions, and individuals with relevant programming experience.
- Restrictions: For-profit entities and commercial media organizations are ineligible.
- Registration: All applicants must have a Unique Entity Identifier (UEI) and be registered on SAM.gov unless exempted.

---

**4. Application Process**

The application process consists of a two-step submission:
1. Statement of Interest (SOI): Applicants must submit a detailed SOI outlining the proposed program.
2. Full Proposal: Successful SOIs will be invited to submit a full proposal, including SF-424 forms for federal assistance and detailed budget information.

---

**5. Evaluation Criteria**

Proposals will be evaluated based on the following criteria:
- Alignment with program objectives
- Demonstrated impact on literacy development
- Feasibility and sustainability of the program
- Budget efficiency and effectiveness

---

**6. Budget Information**

The total funding available for this program is approximately $200,000, with awards ranging from $25,000 to $100,000. Exceptional proposals above $200,000 may be considered based on funding availability.

---

**7. Conclusion**

In conclusion, this proposal introduces Boost Reading as a valuable resource for supporting literacy development and enhancing educational outcomes. By leveraging Boost Reading's research-based approach to literacy instruction, educators can provide students with engaging and effective learning experiences tailored to their individual needs. We believe that our proposed initiatives align with the objectives of the funding opportunity and will have a significant impact on promoting literacy growth and cultural ties between the U.S. and Ethiopia.

---

**[Insert Contact Information]**

---

**[Your Company Logo]**
"""

# Define your prompt suffix
prompt_suffix = """
can you rewrite the consuion
"""

# Call the function
rewritten_text = rewrite_text(input_text, prompt_suffix)
print(rewritten_text)





def rewrite_text(input_text: str, prompt_suffix: str) -> str:
    prompt = f"""
    You are an AI assistant here to help with anything requested.

    Input text: {input_text}

    Prompt to change the input text: {prompt_suffix}

    Please combine the input text and the prompt_suffix to create a new, cohesive text.
    """
    
    response = llm.invoke(prompt)
    return response.content
