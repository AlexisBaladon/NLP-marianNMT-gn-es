from src.config.config import load_config_variables, \
    COMMAND_NAME, \
    FLAG_SEPARATOR, \
    BASE_DIR_EVALUATION
from src.utils.parsing import deep_copy_flags

class CommandConfig:
    def __init__(self, 
                 command_name, 
                 command_path, 
                 flags, 
                 flag_separator, 
                 train_from_epoch=0,
                 validate_each_epochs=None, 
                 validation_metrics=None, 
                 save_checkpoints=False, 
                 results_dir=None, 
                 base_dir_evaluation=None,
                 not_delete_model_after=False,
                 run_id=None):
        # type: (str, str, dict, str, str, int, list[str], bool, str, str, bool, str) -> None
        self.command_name = command_name
        self.command_path = command_path
        self.flags = flags
        self.flag_separator = flag_separator
        self.train_from_epoch = train_from_epoch
        self.validate_each_epochs = validate_each_epochs
        self.validation_metrics = validation_metrics
        self.save_checkpoints = save_checkpoints
        self.results_dir = results_dir
        self.base_dir_evaluation = base_dir_evaluation
        self.not_delete_model_after = not_delete_model_after
        self.run_id = run_id

    def copy(self, deep=False):
        # type: (bool) -> CommandConfig
        return CommandConfig(command_name=self.command_name,
                             command_path=self.command_path,
                             flags=deep_copy_flags(self.flags) if deep else self.flags,
                             flag_separator=self.flag_separator,
                             train_from_epoch=self.train_from_epoch,
                             validate_each_epochs=self.validate_each_epochs,
                             validation_metrics=deep_copy_flags(self.validation_metrics) if deep else self.validation_metrics,
                             save_checkpoints=self.save_checkpoints,
                             results_dir=self.results_dir,
                             base_dir_evaluation=self.base_dir_evaluation,
                             not_delete_model_after=self.not_delete_model_after,
                             run_id=self.run_id)
    
    def __str__(self):
        # type: () -> str
        return "CommandConfig(command_name={}, command_path={}, flags={}, flag_separator={}, train_from_epoch={} validate_each_epochs={}, validation_metrics={}, save_checkpoints={}, results_dir={}, base_dir_evaluation={}, not_delete_model_after={}, run_id={})".format(
            self.command_name,
            self.command_path,
            self.flags,
            self.flag_separator,
            self.train_from_epoch,
            self.validate_each_epochs,
            self.validation_metrics,
            self.save_checkpoints,
            self.results_dir,
            self.base_dir_evaluation,
            self.not_delete_model_after,
            self.run_id)
    
    def __repr__(self):
        # type: () -> str
        return str(self)

def get_command_config(command_path, 
                       flags, 
                       validate_each_epochs=None, 
                       validation_metrics=None, 
                       save_checkpoints=False, 
                       results_dir=None, 
                       not_delete_model_after=False,
                       run_id=None):
    # type: (str, dict, int, list[str], bool, str, bool, str) -> CommandConfig
    config_variables = load_config_variables()
    return CommandConfig(command_name=config_variables[COMMAND_NAME],
                         command_path=command_path,
                         flags=flags,
                         flag_separator=config_variables[FLAG_SEPARATOR],
                         validate_each_epochs=validate_each_epochs,
                         validation_metrics=validation_metrics,
                         save_checkpoints=save_checkpoints,
                         results_dir=results_dir,
                         base_dir_evaluation=config_variables[BASE_DIR_EVALUATION],
                         not_delete_model_after=not_delete_model_after,
                         run_id=run_id)