# Setting Up Credentials for Course Link Checker

This document explains how to set up credentials for the course link checker using a `.env` file.

## Setup Instructions

### 1. Create the `.env` file

Copy the example file to `.env` and fill in your actual credentials:

```bash
cp .env.example .env
```

Then edit `.env` with your university credentials:

```env
# University of Greifswald (UG)
CC_USER_UG=your_ug_username
CC_PW_UG=your_ug_password

# IPT - Polytechnic University of Tomar
CC_USER_IPT=your_ipt_username
CC_PW_IPT=your_ipt_password

# BUas - Breda University of Applied Sciences
CC_USER_BUAS=your_buas_username
CC_PW_BUAS=your_buas_password

# ATU - Adana Alparslan Türkeş Science and Technology University
CC_USER_ATU=your_atu_username
CC_PW_ATU=your_atu_password

# TAE - D. A. Tsenov Academy of Economics
CC_USER_TAE=your_tae_username
CC_PW_TAE=your_tae_password

# OUTech - Opole University of Technology
CC_USER_OUTech=your_outech_username
CC_PW_OUTech=your_outech_password

# SH - Södertörn University
CC_USER_SH=your_sh_username
CC_PW_SH=your_sh_password

# UNICAM - University of Camerino
CC_USER_UNICAM=your_unicam_username
CC_PW_UNICAM=your_unicam_password

# USB - University of South Bohemia
CC_USER_USB=your_usb_username
CC_PW_USB=your_usb_password

# TUT - University of Trnava
CC_USER_TUT=your_tut_username
CC_PW_TUT=your_tut_password

# VUT - Valahia University of Târgovište
CC_USER_VUT=your_vut_username
CC_PW_VUT=your_vut_password
```

### 2. Supported Universities

| Code  | University                                    |
|-------|-----------------------------------------------|
| ATU   | Adana Alparslan Türkeş Science and Technology |
| BUas  | Breda University of Applied Sciences          |
| TAE   | D. A. Tsenov Academy of Economics             |
| OUTech| Opole University of Technology                |
| IPT   | Polytechnic University of Tomar               |
| SH    | Södertörn University                          |
| UNICAM| University of Camerino                        |
| UG    | University of Greifswald                      |
| USB   | University of South Bohemia                   |
| TUT   | University of Trnava                          |
| VUT   | Valahia University of Târgovište              |

### 3. Credential Format

Each university requires two environment variables:

- `CC_USER_{UNIVERSITY}`: Username for LMS access
- `CC_PW_{UNIVERSITY}`: Password for LMS access

Example: `CC_USER_UG=myusername`, `CC_PW_UG=mypassword`

Only the credentials you fill in will be used. Leave placeholders for universities you don't need.

## Security Note

- **Never commit `.env` to version control** - it is already in `.gitignore`
- Use the `.env.example` file as a template with placeholder values
- Keep your credentials secure and never share them

## Example Usage

```bash
uv run data_checks/check_course_links.py data/course.json
``