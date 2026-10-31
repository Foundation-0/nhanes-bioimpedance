# Repository description and topics

`repository-metadata.json` records the proposed description and topics. These are GitHub settings, so a file
commit alone does not apply them. A maintainer sets them in the repository settings.

Read the live values with:

```sh
gh api repos/Foundation-0/nhanes-bioimpedance --jq '{description, topics}'
```
