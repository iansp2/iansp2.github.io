---
icon: lucide/scroll-text
---

# Vim

As with most cheatsheets here, it is not meant to be exhaustive. It's just things I use often enough that I want to have it easily accessible, but not often enough that I memorized it.

``` 
# When I accidentally hit #, vim searches for that term and highlights every instance of it. This removes the highlight.
:noh

# Copying from vim to somewhere else can be a pain. This solves it. Enter visual mode and then hit the following sequence.
# Note that + here means literally typing it, as opposed to indicating the combination between two keys
"+y

# Enter hex mode to edit specific bytes in a binary (e.g., a header)
:%!xxd

# Exit hex mode
:%!xxd -r

# Sort selection alphabetically (e.g., python imports)
:sort
```
