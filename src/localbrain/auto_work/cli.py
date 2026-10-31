from __future__ import annotations
from localbrain.foundation.validation import ExperimentError
from localbrain.experiments.reconstruction.experiment import QuietParser
from localbrain.auto_work.preview import prepare_preview


def main(argv=None):
    parser = QuietParser(description="Prepare the local Auto Work preview explicitly.")
    parser.add_argument("--database", required=True)
    parser.add_argument("--cache-dir", "--data-dir", dest="data_dir", required=True)
    try:
        args = parser.parse_args(argv)
        prepare_preview(args.database, args.data_dir)
        print("AUTO_WORK_PREVIEW_READY")
        return 0
    except KeyboardInterrupt:
        print("AUTO_WORK_PREVIEW_CANCELLED")
        return 130
    except Exception as error:
        if isinstance(error, ExperimentError) and str(error) == "PREVIEW_BUSY":
            print("AUTO_WORK_PREVIEW_BUSY")
            return 3
        print("AUTO_WORK_PREVIEW_FAILED")
        return 2
