"""Explicit generation contracts inspected against live ToAPIs catalog, 2026-10-14."""
MODEL_ROUTES={
 'gpt-image-2-vip':{'quality':'low','resolution':'1K','resolution_field':'top','quoted_input_count':0},
 'gpt-image-2':{'quality':None,'resolution':'1K','resolution_field':'both','quoted_input_count':0},
 'gpt-image-2.5-flare':{'quality':'high','resolution':'1K','resolution_field':'metadata','quoted_input_count':0},
 'gemini-nano-banana-2.1':{'quality':None,'resolution':'1K','resolution_field':'metadata','quoted_input_count':0},
 'doubao-seedream-5-0-pro':{'quality':'medium','resolution':'1K','resolution_field':'both','quoted_input_count':1},
 'gemini-3.1-flash-image-preview':{'quality':None,'resolution':'1K','resolution_field':'metadata','quoted_input_count':0},
 'nano_banana':{'quality':None,'resolution':'1K','resolution_field':'metadata','quoted_input_count':0},
}
# Seedream docs: first reference is free; catalog floor is input_image_count=1.
# Only VIP reference edits have been validated. Other routes are generation-only.

MODEL_ROUTES['doubao-seedream-5-0-pro-global']={'quality':None,'resolution':'1K','resolution_field':'both','quoted_input_count':0}
