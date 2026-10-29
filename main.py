"""GeoRush GUI and repeatable offline command-line runner."""
from __future__ import annotations

import argparse
import json
import multiprocessing
from pathlib import Path


def main(argv=None):
    parser = argparse.ArgumentParser(description="GeoRush Generator — local flag quiz Shorts")
    parser.add_argument("--mode", choices=("Shorts", "Longform"), default="Shorts")
    parser.add_argument("--generate", type=int, choices=(1, 2, 3, 5, 10), help="Generate a batch without the GUI")
    parser.add_argument("--difficulty", choices=("Easy", "Normal", "Hard", "Mixed"), default="Mixed")
    parser.add_argument("--questions", type=int)
    parser.add_argument("--bgm", type=float, choices=(0.08, 0.10, 0.12), default=0.10)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--seed", type=int, help="Reproducible test selection; history still prevents repeated quizzes")
    parser.add_argument("--gui-smoke", action="store_true", help="Open and close GUI without generating videos")
    parser.add_argument('--longform-check', type=Path, help='Exercise packaged Longform GUI and decode')
    parser.add_argument('--distribution-check', type=Path, metavar='REPORT_JSON', help='Exercise real packaged GUI and MP4 generation')
    args = parser.parse_args(argv)
    if args.longform_check:
        from georush.longform.distribution_check import run_check
        return run_check(args.longform_check,args.output)
    if args.distribution_check:
        from georush.distribution_check import run_check
        return run_check(args.distribution_check, args.output)
    if args.gui_smoke:
        from georush.gui import GeoRushApp
        app = GeoRushApp()
        app.after(400, app.destroy)
        app.mainloop()
        print(json.dumps({"gui_created_and_closed": True, "video_generation": False}))
        return 0
    if args.generate is not None:
        from georush.paths import default_output_root
        if args.mode == 'Longform':
            from georush.longform.pipeline import generate_batch
        else:
            from georush.pipeline import generate_batch
        rows = generate_batch(count=args.generate, difficulty=args.difficulty, questions_per_video=args.questions if args.questions is not None else (40 if args.mode=="Longform" else 3),
                              bgm_volume=args.bgm, output_root=args.output or default_output_root(),
                              progress_callback=lambda event: print(json.dumps(event, ensure_ascii=False), flush=True),
                              seed=args.seed)
        print(json.dumps({"results": rows}, ensure_ascii=False, indent=2))
        return 0 if all(row.get("status") == "success" for row in rows) else 1
    from georush.gui import launch
    launch()
    return 0


if __name__ == "__main__":
    multiprocessing.freeze_support()
    raise SystemExit(main())
