from types import FunctionType
from typing import Generator
from pathlib import Path
from time import sleep as wait


class BaseCleaner:
    class Meta:
        abstract = True

    DEFAULT_BASE_DIR = Path(__file__).absolute().parent.parent
    EMPTY = ''
    BASE_DIR = EMPTY
    VALID_OPTIONS = (1, 2)
    ERROR_DICT = {
        '_404_ERROR': ('%s is not a valid file path on your machine,\n'
                       'Kindly review path provided and ensure there is no typo'),

        'VERBOSE_ERROR': ('verbose argument must be of class %s'
                          ' not class %s')
    }

    def __init__(self, base_dir: Path | str = None, *args, **kwargs):
        # If base_dir is not passed default to the parent folder of the module
        # equivalent to cd ../.. from this module's absolute path
        if not base_dir:
            def set_base_dir():
                self.BASE_DIR = self.DEFAULT_BASE_DIR
            info = 'No base_dir was provided, do you want to proceed with the DEFAULT_BASE_DIR?'
            # Get feedback from a user, display a prompt
            # asking if they would want to set the BASE_DIR to
            # DEFAULT_BASE_DIR
            self.__get_feedback__(info, yes=set_base_dir)
        else:
            self.set_base_dir(base_dir)
        # Get the verbose argument, defaults to False if not passed
        self.VERBOSE = kwargs.pop('verbose', True)
        # Run internal checks to verify the integrity of
        # or properties before cleaning commences
        self.__run_checks__()

    def __run_checks__(self, fail_silently=False) -> dict | None:
        """

        Checks the internal state of this object,
        validates the `BASE_DIR` and `VERBOSE` properties

        * Args:
            `fail_silently` (bool, optional): Determines how failures are
            handled during checks.

            `Defaults` to `False`.

        * Raises:

            `FileNotFoundError`: Raised if `BASE_DIR` is not found
            and `fail_silently` is False

            `TypeError`: Raised if the `VERBOSE` property has invalid
            `type` and `fail_silently` is False

        * Returns:

            `dict` | `None` : {`field_name`:`str`, `is_validated`:`bool`, 'message':`str`}
            if checks fail and `fail_silently` is True

           `None` if checks fail and `fail_silently` is False


        """
        if not self.BASE_DIR.exists():
            if fail_silently:
                return {
                    'field_name': 'BASE_DIR',
                    'is_validated': False,
                    'message': self.ERROR_DICT.get('_404_ERROR') % self.BASE_DIR,
                }
            raise FileNotFoundError(
                self.ERROR_DICT.get('_404_ERROR') % self.BASE_DIR
            )

        if not isinstance(self.VERBOSE, bool):
            if fail_silently:
                return {'field_name': 'VERBOSE',
                        'is_validated': False,
                        'message': self.ERROR_DICT.get(
                            'VERBOSE_ERROR') % (bool,
                                                self.VERBOSE.__class__
                                                ),
                        }
            raise TypeError(self.ERROR_DICT.get('VERBOSE_ERROR') %
                            (bool, self.VERBOSE.__class__))
        # If code execution gets here return True as this
        # implies all checks ran successfully
        return {
            'field_name': None,
            'is_validated': True,
            'message': 'Internal checks ran successfully',
        }
        
    def _convert_valid_options_to_string(cls) -> str | None:
        # Ensure the VALID_OPTIONS property was not tampered with
        if len(cls.VALID_OPTIONS) < 1:
            raise ValueError(
                'VALID_OPTIONS must be decalred'
                'or left to the default'
                'It can not be empty'
            )
        # Convert all options to string irrespective of their original type
        cls.VALID_OPTIONS = tuple(map(lambda option: str(option), cls.VALID_OPTIONS))
        if len(cls.VALID_OPTIONS) == 2:
            return '%s or %s' % (cls.VALID_OPTIONS[0], cls.VALID_OPTIONS[1])
        # Format to look like this:
        # If a tuple containing 4 elements was passed in say we had
        # (1, 2, 3, 4), our output would be a string object
        # whose value would be like this: 1, 2, 3 or 4
        return ', '.join(cls.VALID_OPTIONS[:-1]) + ', or %s' % cls.VALID_OPTIONS[-1]

    def __get_feedback__(cls, info: str, yes: FunctionType, no: FunctionType = lambda: exit(0), no_of_trials: int = 3) -> None:
        # Set VERBOSE to True so as to display info to stdout
        # via the __separate_msg__ function
        cls.VERBOSE = True
        options_string = cls._convert_valid_options_to_string()
        options = '\n1) Yes\n2) No\n>>> '
        # Display the info before iteration begins
        # to avoid unnecessary display of info
        print(info)
        for num in range(no_of_trials):
            final_trial = num == no_of_trials - 1
            if final_trial:
                # Display this warning during final iteration
                # after user must have entered invalid options
                # for a total of (no_of_trials - 1) times
                options = 'This is your last trial' + options
            feedback = input(options)
            if feedback not in cls.VALID_OPTIONS:
                # Do not display this during final iteration
                if not final_trial:
                    cls.__separate_msg__(
                        'Provided option "%s" is invalid, Kindly input one of the following %s'%(feedback, options_string))
                    print('Choose an option, %s' % options_string)
                continue

            if feedback == '1':
                cls.__separate_msg__(
                    'Defaulting to %s as BASE_DIR' % cls.DEFAULT_BASE_DIR)
                yes()
                return

            if feedback == '2':
                cls.__separate_msg__('Exiting application...')
                no()
        # If code executes to this point it means all
        # attempts to get valid feedback from the user
        # failed, we display a message to inform them
        # that the program is about to be exited
        cls.__separate_msg__('Too many invalid attempts',
                             'Exiting application...')
        # Finally, call the no function to close application
        no()

    def __separate_msg__(self, *msg) -> None:
        """Create a separator beneath `msg` to aid
        cleaner output

        Args:
            `msg` (str): Message(s) to display to stdout
        """
        if self.VERBOSE:
            [print(_msg, self.EMPTY) for _msg in msg]
            print('-'*100)
            wait(1)

    def _discover_paths(self, *, pattern: str = '*', directory_only=False, exclude_hidden=False) -> Generator:
        # Check if a str object was passed as argument
        # and cast it to a Path object
        discovered_paths = self.BASE_DIR.iterdir()
        if directory_only:
            discovered_paths = filter(lambda discovered_path: discovered_path.is_dir(),
                                      discovered_paths)

        if exclude_hidden:
            # Use re to match all paths with a . in the current path
            # negate the expression to get only unhidden files and directories
            discovered_paths = filter(
                lambda discovered_path: not discovered_path.match(r'*\.*'), discovered_paths)

        if self.VERBOSE:
            header = 'Path(s) discovered at %s' % self.BASE_DIR
            dir_only_msg = 'Displaying directories only' if directory_only else ''
            msg = '\n'.join(
                list(map(lambda discovered_path: discovered_path.__str__(), discovered_paths)))
            self.__separate_msg__(header, dir_only_msg, msg)
        return discovered_paths

    async def remove_files(self, dir: Path, pattern: str) -> int:
        pass

    def set_base_dir(self, base_dir: Path | str, *, run_checks: bool = False) -> None:
        """Sets the instance's `BASE_DIR` to a new file path
        provided by the `base_dir` argument

        * Args:
            `base_dir` (`Path` | `str`): A new `Path` or `str` instance desired to
            be used as the new `BASE_DIR`


        * Kwargs:
            `run_checks` (`bool`): Flag to signal re-running checks
            upon change of `BASE_DIR`, Defaults to `False`

        """
        # Store the current BASE_DIR property in a
        # TEMP_BASE_DIR variable if it is not None,
        # use this as a fallback strategy incase the
        # new BASE_DIR fails to pass checks
        if self.BASE_DIR:
            TEMP_BASE_DIR = self.BASE_DIR
        self.BASE_DIR = Path(base_dir).resolve()
        # Return at this point if we are not running checks
        if not run_checks:
            return
        # Do not raise exceptions if the checks fail instead get
        # field_name and message, display them to stdout
        field_name, is_validated, message = self.__run_checks__(
            fail_silently=True).values()
        if self.VERBOSE:
            if is_validated:
                header = 'Validation of new BASE_DIR was successful'
                footer = 'BASE_DIR is now set to:\n%s' % self.BASE_DIR
            else:
                header = 'Validation of %s failed...' % field_name
                footer = 'Reverting to previously valid BASE_DIR\n%s' % TEMP_BASE_DIR
                # Upon failure fall back to previous BASE_DIR
                self.BASE_DIR = TEMP_BASE_DIR
            self.__separate_msg__(header, self.EMPTY,
                                  message, self.EMPTY, footer)

    # To achieve Singleton design pattern for
    # this class we override the "__new__" dunder method
    def __new__(cls, base_dir: Path | str = None, *args, **kwargs):
        # Check if an instance exists,
        # if none exists we instantiate one by calling
        # the super method of the object class
        if not hasattr(cls, 'instance'):
            cls.instance = super(BaseCleaner, cls).__new__(cls)
        return cls.instance


if __name__ == '__main__':
    c = BaseCleaner()
